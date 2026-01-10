from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Attendance, CheckConfig
from leaves.models import LeaveRequest
from users.models import User
import json
from json import JSONDecodeError


# ---------------------- 工具函数：逻辑重构 ----------------------

def get_check_latest_dt(check_config):
    """
    获取查寝时间点。
    注意：模型字段需为 DateTimeField，存储带时区的完整时间。
    """
    n_start_dt = check_config.normal_start
    n_end_dt = check_config.normal_end
    # 最终截止时间：如果有晚归则取晚归，否则取正常结束
    latest_dt = check_config.late_end if check_config.late_end else n_end_dt
    return latest_dt, n_end_dt, n_start_dt


def get_valid_students(check_config):
    """获取本次查寝需参与的学生（排除校外+请假交集学生）"""
    latest_dt, _, start_dt = get_check_latest_dt(check_config)

    # 交集判定：请假开始 < 查寝结束 AND 请假结束 > 查寝开始
    exclude_ids = LeaveRequest.objects.filter(
        status="approved",
        start_time__lt=latest_dt,
        end_time__gt=start_dt
    ).values_list("student_id", flat=True)

    valid_students = User.objects.filter(
        role="student",
        dorm_type="internal",
        dormitory__isnull=False
    ).exclude(id__in=exclude_ids)

    return valid_students, latest_dt


# ---------------------- 教师端：查寝配置接口 ----------------------

class CheckConfigView(APIView):
    """创建查寝配置（绝对时间点模式）"""

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录"}, status=status.HTTP_401_UNAUTHORIZED)
        if request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        try:
            params = request.data if isinstance(request.data, dict) else json.loads(request.body)

            # 1. 获取并解析字符串为 aware datetime
            # 期望格式: "2026-01-10 21:00"
            fmt = "%Y-%m-%d %H:%M"
            n_start = timezone.make_aware(datetime.strptime(params.get("normal_start"), fmt))
            n_end = timezone.make_aware(datetime.strptime(params.get("normal_end"), fmt))

            l_end = None
            if params.get("late_end"):
                l_end = timezone.make_aware(datetime.strptime(params.get("late_end"), fmt))

            # 2. 严格时间逻辑校验
            if n_start >= n_end:
                return Response({"detail": "开始时间必须早于正常结束时间"}, status=status.HTTP_400_BAD_REQUEST)
            if l_end and n_end > l_end:
                return Response({"detail": "正常结束时间不能晚于晚归截止时间"}, status=status.HTTP_400_BAD_REQUEST)

            # 3. 创建配置
            config = CheckConfig.objects.create(
                config_name=params.get("config_name"),
                check_date=n_start.date(),  # 仅保留日期部分用于辅助索引
                normal_start=n_start,
                normal_end=n_end,
                late_end=l_end,
                valid_range=params.get("valid_range", 500),
                need_material=params.get("need_material", False),
                is_active=True,
                created_by=request.user
            )

            return Response({
                "id": config.id,
                "msg": "配置创建成功",
                "times": {
                    "start": n_start.strftime(fmt),
                    "normal_end": n_end.strftime(fmt),
                    "late_end": l_end.strftime(fmt) if l_end else "未设置"
                }
            }, status=status.HTTP_201_CREATED)

        except (ValueError, TypeError):
            return Response({"detail": "时间格式应为 YYYY-MM-DD HH:MM"}, status=status.HTTP_400_BAD_REQUEST)
        except JSONDecodeError:
            return Response({"detail": "JSON格式错误"}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------- 学生端：打卡接口 ----------------------

class AttendanceView(APIView):
    """学生查寝打卡（兼容跨天逻辑）"""

    def post(self, request):
        if not request.user.is_authenticated or request.user.role != "student":
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        data = request.data

        try:
            config_id = data.get("check_config_id")
            lat, lng = float(data.get("lat")), float(data.get("lng"))
            config = CheckConfig.objects.get(id=config_id, is_active=True)
        except (CheckConfig.DoesNotExist, TypeError, ValueError):
            return Response({"detail": "配置无效或参数错误"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. 时间校验
        now = timezone.localtime(timezone.now())
        latest_dt, n_end_dt, n_start_dt = get_check_latest_dt(config)

        if now < n_start_dt:
            return Response({"detail": "打卡尚未开始"}, status=status.HTTP_400_BAD_REQUEST)
        if now > latest_dt:
            return Response({"detail": "打卡已截止"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 请假校验（实时交集判定）
        if LeaveRequest.objects.filter(
                student_id=user.id, status="approved",
                start_time__lt=latest_dt, end_time__gt=n_start_dt
        ).exists():
            return Response({"detail": "您在请假期间，无需打卡"}, status=status.HTTP_200_OK)

        # 3. 位置与材料校验
        if not user.dormitory:
            return Response({"detail": "未绑定宿舍"}, status=status.HTTP_400_BAD_REQUEST)

        from .utils import haversine
        dist = haversine(lng, lat, float(user.dormitory.longitude), float(user.dormitory.latitude))
        if dist > config.valid_range:
            return Response({"detail": f"位置超限({round(dist)}米)"}, status=status.HTTP_400_BAD_REQUEST)

        if config.need_material and not request.FILES.get("material"):
            return Response({"detail": "需上传证明材料"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. 判定状态与保存
        status_code = "normal" if now <= n_end_dt else "late"
        if status_code == "late" and not data.get("late_reason"):
            return Response({"detail": "请填写晚归理由"}, status=status.HTTP_400_BAD_REQUEST)

        if Attendance.objects.filter(student=user, check_config=config).exists():
            return Response({"detail": "请勿重复打卡"}, status=status.HTTP_200_OK)

        Attendance.objects.create(
            student=user, student_name=user.get_full_name() or user.username,
            dorm=user.dormitory, check_config=config,
            lat=lat, lng=lng, distance=dist, check_time=now,
            check_status=status_code, late_reason=data.get("late_reason", ""),
            material=request.FILES.get("material")
        )

        return Response({"msg": "打卡成功", "status": status_code}, status=status.HTTP_201_CREATED)


# ---------------------- 教师端：统计接口 ----------------------

class AttendanceStatisticsView(APIView):
    """教师查看统计（自动适配绝对时间阶段）"""

    def get(self, request):
        if not request.user.is_authenticated or request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        config_id = request.query_params.get("check_config_id")
        try:
            config = CheckConfig.objects.get(id=config_id)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "配置不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 1. 确定当前阶段
        now = timezone.localtime(timezone.now())
        latest_dt, n_end_dt, n_start_dt = get_check_latest_dt(config)

        if now < n_end_dt:
            stage, stage_desc = 1, "正常打卡中"
        elif config.late_end and now < latest_dt:
            stage, stage_desc = 2, "晚归打卡中"
        else:
            stage, stage_desc = 3, "查寝已结束"

        # 2. 汇总数据
        valid_students, _ = get_valid_students(config)
        records = Attendance.objects.filter(check_config=config)
        checked_ids = records.values_list("student_id", flat=True)

        # 3. 构造返回
        response_data = {
            "config_info": {
                "name": config.config_name,
                "stage": stage,
                "stage_desc": stage_desc,
                "range": f"{n_start_dt.strftime('%H:%M')} - {n_end_dt.strftime('%H:%M')}"
            },
            "statistics": {
                "total": valid_students.count(),
                "normal": records.filter(check_status="normal").count(),
                "late": records.filter(check_status="late").count(),
                "absent": valid_students.exclude(id__in=checked_ids).count()
            },
            "lists": {
                "normal": self._format(records.filter(check_status="normal")),
                "late": self._format(records.filter(check_status="late"), True),
                "absent": [{"name": s.username, "id": s.student_id} for s in valid_students.exclude(id__in=checked_ids)]
            }
        }
        return Response(response_data)

    def _format(self, qs, show_reason=False):
        return [
            {
                "name": r.student_name,
                "time": r.check_time.strftime("%H:%M:%S"),
                "reason": r.late_reason if show_reason else ""
            } for r in qs
        ]