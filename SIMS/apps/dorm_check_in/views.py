from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from .models import Attendance, CheckConfig
from leaves.models import LeaveRequest
from users.models import User
import json
from json import JSONDecodeError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CheckConfig
from .serializers import CheckConfigListSerializer


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
    """
    查寝配置接口
    GET: 获取所有查寝任务列表（含动态进行状态）
    POST: 教师创建新任务
    """

    def get(self, request):
        """返回所有查寝任务，包含实时计算的状态"""
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录"}, status=status.HTTP_401_UNAUTHORIZED)

        # 1. 获取所有查寝任务记录（按时间倒序排列，最新的在前面）
        configs = CheckConfig.objects.all().order_by('-normal_start')

        # 2. 构造返回列表
        # 这里的 config.current_status 和 config.status_display 会在执行这一行时实时对比当前时间
        data = [
            {
                "config_id": config.id,
                "config_name": config.config_name,
                "check_date": config.check_date,
                "normal_start": config.normal_start.strftime("%Y-%m-%d %H:%M"),
                "normal_end": config.normal_end.strftime("%Y-%m-%d %H:%M"),
                "late_end": config.late_end.strftime("%Y-%m-%d %H:%M") if config.late_end else None,
                "status": config.current_status,         # 动态属性：'not_started', 'in_progress', 'ended'
                "status_desc": config.status_display,    # 动态属性：'未开始', '进行中', '已结束'
                "need_material": config.need_material,
                "valid_range": config.valid_range
            }
            for config in configs
        ]

        return Response(data, status=status.HTTP_200_OK)

    # 2. 创建任务
    def post(self, request):
        if not request.user.is_authenticated or request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        try:
            params = request.data if isinstance(request.data, dict) else json.loads(request.body)
            fmt = "%Y-%m-%d %H:%M"
            n_start = timezone.make_aware(datetime.strptime(params.get("normal_start"), fmt))
            n_end = timezone.make_aware(datetime.strptime(params.get("normal_end"), fmt))

            l_end = None
            if params.get("late_end"):
                l_end = timezone.make_aware(datetime.strptime(params.get("late_end"), fmt))

            if n_start >= n_end:
                return Response({"detail": "开始时间必须早于正常结束时间"}, status=status.HTTP_400_BAD_REQUEST)

            config = CheckConfig.objects.create(
                config_name=params.get("config_name"),
                check_date=n_start.date(),
                normal_start=n_start,
                normal_end=n_end,
                late_end=l_end,
                valid_range=params.get("valid_range", 500),
                need_material=params.get("need_material", False),
                created_by=request.user
            )

            # 返回时直接读取属性即可
            return Response({
                "id": config.id,
                "msg": "配置创建成功",
                "status": config.current_status,  # 动态属性
                "status_desc": config.status_display  # 动态属性
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ---------------------- 学生端：打卡接口 ----------------------

class AttendanceView(APIView):
    """学生查寝打卡"""

    def post(self, request):
        # 1. 权限与参数获取
        if not request.user.is_authenticated or request.user.role != "student":
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        config_id = request.data.get("check_config_id")

        try:
            config = CheckConfig.objects.get(id=config_id, is_active=True)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "配置无效"}, status=status.HTTP_400_BAD_REQUEST)

        # ---------------------------------------------------------
        # 2. 【核心修改】首先判断任务状态 (利用 models 中的动态属性)
        # ---------------------------------------------------------
        current_status = config.current_status  # 调用 Model 中的 property

        if current_status == 'not_started':
            return Response({
                "detail": f"打卡尚未开始",
                "task_status": "not_started"
            }, status=status.HTTP_400_BAD_REQUEST)

        if current_status == 'ended':
            return Response({
                "detail": "打卡已结束，您已无法打卡",
                "task_status": "ended"
            }, status=status.HTTP_400_BAD_REQUEST)

        # --- 以下代码仅在 current_status == 'in_progress' 时执行 ---

        # 3. 基础逻辑校验（校外、宿舍绑定）
        if user.dorm_type == "external":
            return Response({"detail": "校外住宿无需打卡"}, status=status.HTTP_200_OK)
        if not user.dormitory:
            return Response({"detail": "未绑定宿舍"}, status=status.HTTP_400_BAD_REQUEST)
        if Attendance.objects.filter(student=user, check_config=config).exists():
            return Response({"detail": "请勿重复打卡"}, status=status.HTTP_200_OK)

        # 4. 请假校验（实时交集判定）
        # 再次获取时间是为了进行精确的区间对比
        latest_dt = config.late_end if config.late_end else config.normal_end
        if LeaveRequest.objects.filter(
                student_id=user.id, status="approved",
                start_time__lt=latest_dt, end_time__gt=config.normal_start
        ).exists():
            return Response({"detail": "您在请假期间，无需打卡"}, status=status.HTTP_200_OK)

        # 5. 位置与材料校验
        lat = float(request.data.get("lat", 0))
        lng = float(request.data.get("lng", 0))
        from .utils import haversine
        dist = haversine(lng, lat, float(user.dormitory.longitude), float(user.dormitory.latitude))

        if dist > config.valid_range:
            print("lng",lng)
            print("lat",lat)
            return Response({"detail": f"位置超限({round(dist)}米)"}, status=status.HTTP_400_BAD_REQUEST)

        if config.need_material and not request.FILES.get("material"):
            return Response({"detail": "需上传证明材料"}, status=status.HTTP_400_BAD_REQUEST)

        # 6. 判定具体是“正常”还是“晚归”
        # 注意：这里不需要再判断是否 ended，因为前面已经拦截了
        now = timezone.localtime(timezone.now())
        status_code = "normal" if now <= config.normal_end else "late"

        if status_code == "late" and not request.data.get("late_reason"):
            return Response({"detail": "当前处于晚归时段，请填写晚归理由"}, status=status.HTTP_400_BAD_REQUEST)

        # 7. 落库保存
        Attendance.objects.create(
            student=user,
            student_name=user.get_full_name() or user.username,
            dorm=user.dormitory,
            check_config=config,
            lat=lat, lng=lng, distance=dist, check_time=now,
            check_status=status_code,
            late_reason=request.data.get("late_reason", ""),
            material=request.FILES.get("material")
        )

        return Response({
            "msg": "打卡成功",
            "status": status_code,
            "check_time": now.strftime('%Y-%m-%d %H:%M:%S')
        }, status=status.HTTP_201_CREATED)


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


class CheckTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    查寝任务列表视图：
    提供给学生和老师查看所有的查寝记录，包含动态状态。
    """
    queryset = CheckConfig.objects.all().order_by('-normal_start')
    serializer_class = CheckConfigListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        根据角色过滤（可选）：
        例如：学生只能看到 is_active=True 的任务，老师能看到所有。
        """
        user = self.request.user
        qs = CheckConfig.objects.all().order_by('-normal_start')

        if user.role == 'student':
            return qs.filter(is_active=True)
        return qs