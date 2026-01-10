from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Attendance, CheckConfig
from leaves.models import LeaveRequest
from users.models import User
import json  # 导入整个json模块，或单独导入异常类
from json import JSONDecodeError  # 推荐：直接导入异常类


# ---------------------- 工具函数：通用逻辑抽离 ----------------------
def get_check_latest_dt(check_config):
    """计算查寝的最晚截止时间（兼容跨天）"""
    check_date = check_config.check_date
    # 拼接正常结束时间
    normal_end_dt = timezone.make_aware(datetime.combine(check_date, check_config.normal_end))
    # 拼接正常开始时间（新增：用于打卡时间校验）
    normal_start_dt = timezone.make_aware(datetime.combine(check_date, check_config.normal_start))
    # 拼接晚归截止时间
    if check_config.late_end:
        if check_config.late_end < check_config.normal_end:
            # 跨天：日期+1
            check_latest_dt = timezone.make_aware(
                datetime.combine(check_date + timedelta(days=1), check_config.late_end))
        else:
            check_latest_dt = timezone.make_aware(datetime.combine(check_date, check_config.late_end))
    else:
        check_latest_dt = normal_end_dt
    return check_latest_dt, normal_end_dt, normal_start_dt


def get_valid_students(check_config):
    """获取本次查寝需参与的学生（排除校外+请假时间段有交集的学生）"""
    # 获取查寝的起始和最晚结束时间（aware datetime）
    check_latest_dt, _, check_start_dt = get_check_latest_dt(check_config)

    # 【核心逻辑修改】：筛选请假时间段与查寝时段有“交集”的已批准申请
    # 交集判定公式：请假开始时间 < 查寝结束时间 AND 请假结束时间 > 查寝开始时间
    exclude_ids = LeaveRequest.objects.filter(
        status="approved",
        start_time__lt=check_latest_dt,  # 请假开始在查寝结束前
        end_time__gt=check_start_dt     # 请假结束在查寝开始后
    ).values_list("student_id", flat=True)

    # 筛选需参与查寝的学生
    valid_students = User.objects.filter(
        role="student",
        dorm_type="internal",
        dormitory__isnull=False
    ).exclude(
        id__in=exclude_ids
    )
    return valid_students, check_latest_dt


# ---------------------- 教师端：查寝配置接口 ----------------------
from datetime import datetime, timedelta


class CheckConfigView(APIView):
    """创建/修改单天查寝配置"""

    def post(self, request):
        # 权限校验保持不变
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录系统"}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ["teacher",  "admin"]:
            return Response({"detail": "仅教师/管理员可配置查寝规则"}, status=status.HTTP_403_FORBIDDEN)

        try:
            params = request.data if isinstance(request.data, dict) else json.loads(request.body)
        except JSONDecodeError:
            return Response({"detail": "请求参数格式错误"}, status=status.HTTP_400_BAD_REQUEST)

        # --- 修改参数校验：使用时长(duration)代替结束时间 ---
        required_fields = ["config_name", "check_date", "normal_start", "normal_duration"]
        for field in required_fields:
            if not params.get(field):
                return Response({"detail": f"{field}为必填项"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. 解析日期和开始时间
            check_date = datetime.strptime(params.get("check_date"), "%Y-%m-%d").date()
            normal_start_time = datetime.strptime(params.get("normal_start"), "%H:%M").time()

            # 2. 将开始时间转为 datetime 以便进行时间加减计算
            start_dt = datetime.combine(check_date, normal_start_time)

            # 3. 获取时长（分钟）
            normal_duration = int(params.get("normal_duration"))
            late_duration = int(params.get("late_duration", 0))

            if normal_duration <= 0:
                return Response({"detail": "正常打卡时长必须大于0"}, status=status.HTTP_400_BAD_REQUEST)

            if late_duration < 0:
                return Response({"detail": "晚归打卡时长必须大于等于0"}, status=status.HTTP_400_BAD_REQUEST)


            # 4. 计算结束时间
            # 正常结束时间 = 开始时间 + 正常时长
            normal_end_dt = start_dt + timedelta(minutes=normal_duration)
            normal_end = normal_end_dt.time()

            # 晚归结束时间 = 正常结束时间 + 晚归时长
            late_end = None
            if late_duration > 0:
                late_end_dt = normal_end_dt + timedelta(minutes=late_duration)
                late_end = late_end_dt.time()

        except ValueError:
            return Response({"detail": "日期格式为YYYY-MM-DD，时间格式为HH:MM，时长为整数"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 校验 valid_range
        try:
            valid_range = int(params.get("valid_range", 500))
            min_valid_range = 50
            if valid_range < min_valid_range:
                valid_range = min_valid_range
        except ValueError:
            return Response({"detail": "有效范围必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
        # 创建配置
        config = CheckConfig.objects.create(
            config_name=params.get("config_name"),
            check_date=check_date,
            normal_start=normal_start_time,
            normal_duration=normal_duration,
            late_duration=late_duration,
            valid_range=valid_range,
            need_material=params.get("need_material", False),
            notify_normal_after_normal_end=params.get("notify_normal_after_normal_end", True),
            notify_late_after_late_end=params.get("notify_late_after_late_end", True) if late_end else False,
            is_active=params.get("is_active", True),
            created_by=request.user
        )


        # 响应：返回计算出的具体时间点供前端确认
        return Response({
            "id": config.id,
            "msg": "查寝配置创建成功",
            "config": {
                "name": config.config_name,
                "date": config.check_date,
                "start_time": normal_start_time.strftime("%H:%M"),
                "normal_end_time": config.normal_end.strftime("%H:%M"),
                "late_end_time": config.late_end.strftime("%H:%M") if config.late_end else "无晚归时段",
                "range": config.valid_range
            }
        }, status=status.HTTP_201_CREATED)


# ---------------------- 学生端：打卡接口 ----------------------
class AttendanceView(APIView):
    """学生查寝打卡"""

    def post(self, request):
        # 1. 捕获JSON解析错误
        try:
            request_data = request.data if isinstance(request.data, dict) else json.loads(request.body)
        except JSONDecodeError:
            return Response({"detail": "请求参数格式错误"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 权限校验
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录系统"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        if user.role != "student":
            return Response({"detail": "仅学生可打卡"}, status=status.HTTP_403_FORBIDDEN)

        # 3. 参数获取与基本校验
        check_config_id = request_data.get("check_config_id")
        lat = request_data.get("lat")
        lng = request_data.get("lng")
        late_reason = request_data.get("late_reason", "").strip()
        material = request.FILES.get("material")

        if not all([check_config_id, lat, lng]):
            return Response({"detail": "参数缺失：需提供配置ID和经纬度"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_config_id = int(check_config_id)
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            return Response({"detail": "参数类型错误"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. 获取查寝配置
        try:
            # 此时 check_config 已经包含了由模型 save() 自动计算出的 normal_end 和 late_end
            check_config = CheckConfig.objects.get(id=check_config_id, is_active=True)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在或未生效"}, status=status.HTTP_404_NOT_FOUND)

        # 5. 获取时间节点
        now = timezone.localtime(timezone.now())
        check_latest_dt, normal_end_dt, normal_start_dt = get_check_latest_dt(check_config)

        # 校验：未到开始时间
        if now < normal_start_dt:
            return Response({
                "detail": f"打卡尚未开始，开始时间：{normal_start_dt.strftime('%m-%d %H:%M')}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 校验：已超过最终截止时间
        if now > check_latest_dt:
            return Response({
                "detail": f"打卡已结束，截止时间：{check_latest_dt.strftime('%m-%d %H:%M')}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 6. 学生身份与状态校验
        if user.dorm_type == "external":
            return Response({"detail": "校外住宿，无需打卡"}, status=status.HTTP_200_OK)

        if not user.dormitory:
            return Response({"detail": "未绑定宿舍楼，请联系管理员"}, status=status.HTTP_400_BAD_REQUEST)
        # 7. 【核心逻辑修改】请假交集校验
        # 即使学生不在 get_valid_students 的初始排除名单中（例如临时批假），打卡时也需再次判定
        leave_exists = LeaveRequest.objects.filter(
            student_id=user.id,
            status="approved",
            start_time__lt=check_latest_dt,  # 请假开始 < 查寝结束
            end_time__gt=normal_start_dt  # 请假结束 > 查寝开始
        ).exists()

        if leave_exists:
            return Response({"detail": "你处于请假期间（请假时段与查寝时段有重合），无需查寝"},
                            status=status.HTTP_200_OK)


        # 8. 位置校验
        dorm = user.dormitory
        try:
            from .utils import haversine
            dist = haversine(lng, lat, float(dorm.longitude), float(dorm.latitude))
        except Exception as e:
            return Response({"detail": f"位置解析异常: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if dist > check_config.valid_range:
            return Response({"detail": f"位置超限（距离{round(dist, 1)}米），请回到宿舍范围内打卡"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 9. 【核心修复】打卡状态判定
        # 因为 normal_end_dt 是 aware datetime，直接比较即可处理跨过 00:00 的情况
        if now <= normal_end_dt:
            check_status = "normal"
        else:
            check_status = "late"
            if not late_reason:
                return Response({"detail": "当前处于晚归时段，请填写晚归理由"}, status=status.HTTP_400_BAD_REQUEST)

        # 10. 重复打卡校验
        if Attendance.objects.filter(student=user, check_config=check_config).exists():
            return Response({"detail": "请勿重复打卡"}, status=status.HTTP_200_OK)

        # 11. 创建记录
        student_name = user.get_full_name() or user.username
        attendance = Attendance.objects.create(
            student=user,
            student_name=student_name,
            dorm=dorm,
            check_config=check_config,
            lat=lat,
            lng=lng,
            distance=dist,
            check_time=now,
            check_status=check_status,
            late_reason=late_reason,
            material=material
        )

        # 修改后的返回结果
        return Response({
            "is_success": True,
            "check_status": attendance.get_check_status_display(),  # 返回"正常打卡"或"晚归打卡"
            "student_name": attendance.student_name,  # 从对象获取姓名
            "student_id": user.student_id,  # 从User对象获取学号
            "distance": round(attendance.distance, 2),  # 保留两位小数
            "check_time": attendance.check_time.strftime('%Y-%m-%d %H:%M:%S'),
            "msg": f"{'正常' if check_status == 'normal' else '晚归'}打卡成功",
            "detail": ""  # 增加空值detail字段
        }, status=status.HTTP_201_CREATED)


# ---------------------- 教师端：实时统计接口 ----------------------
class AttendanceStatisticsView(APIView):
    """教师查看单天查寝的分阶段统计"""

    def get(self, request):
        # 1. 权限校验
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录系统"}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "仅教师/管理员可查看统计数据"}, status=status.HTTP_403_FORBIDDEN)

        # 2. 获取并校验查寝配置
        check_config_id = request.query_params.get("check_config_id")
        if not check_config_id:
            return Response({"detail": "查寝配置ID为必填项"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_config = CheckConfig.objects.get(id=check_config_id)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 3. 获取时间节点（本地时间）
        now = timezone.localtime(timezone.now())
        check_latest_dt, normal_end_dt, normal_start_dt = get_check_latest_dt(check_config)

        # 4. 基础数据准备
        valid_students, _ = get_valid_students(check_config)
        total_count = valid_students.count()


        # 已打卡记录
        checked_records = Attendance.objects.filter(check_config=check_config)
        checked_student_ids = checked_records.values_list("student__student_id", flat=True)

        # 5. 阶段判定逻辑
        if now < normal_end_dt:
            stage = 1
            stage_desc = "正常签到进行中"
        elif check_config.late_end and now < check_latest_dt:
            stage = 2
            stage_desc = "正常签到已结束，晚归签到中"
        else:
            stage = 3
            stage_desc = "查寝已全部结束"

        # 6. 构造返回数据模型
        # 包含配置信息
        response_data = {
            "config_info": {
                "config_id": check_config.id,
                "config_name": check_config.config_name,
                "check_date": check_config.check_date,
                "normal_range": f"{check_config.normal_start.strftime('%H:%M')} 至 {check_config.normal_end.strftime('%H:%M')}",
                "late_end": check_config.late_end.strftime('%H:%M') if check_config.late_end else "无晚归设置",
                "stage": stage,
                "stage_desc": stage_desc
            },
            "statistics": {
                "total_students": total_count,
                "normal_count": 0,
                "late_count": 0,
                "absent_count": 0
            },
            "lists": {
                "normal_list": [],
                "late_list": [],
                "absent_list": []
            }
        }

        # 7. 分类提取名单数据
        # 正常已归
        normal_qs = checked_records.filter(check_status="normal")
        response_data["statistics"]["normal_count"] = normal_qs.count()
        response_data["lists"]["normal_list"] = self._format_student_list(normal_qs)

        # 晚归名单 (仅在阶段 2 和 阶段 3 显示)
        if stage >= 2:
            late_qs = checked_records.filter(check_status="late")
            response_data["statistics"]["late_count"] = late_qs.count()
            response_data["lists"]["late_list"] = self._format_student_list(late_qs, include_reason=True)

        # 未归名单 (总人数 - 所有已打卡人数)
        absent_qs = valid_students.exclude(student_id__in=checked_student_ids)
        response_data["statistics"]["absent_count"] = absent_qs.count()
        # 根据要求，每个阶段都汇报未归名单
        response_data["lists"]["absent_list"] = [
            {
                "student_id": s.student_id,
                "student_name": s.get_full_name() or s.username,
                "dorm": s.dormitory.name if s.dormitory else "未绑定",
                "room": s.address
            } for s in absent_qs
        ]

        return Response(response_data, status=status.HTTP_200_OK)

    def _format_student_list(self, queryset, include_reason=False):
        """辅助函数：格式化已打卡学生列表"""
        data_list = []
        for item in queryset:
            info = {
                "student_id": item.student.student_id,
                "student_name": item.student_name,
                "dorm": item.dorm.name,
                "room": item.student.address,
                "check_time": item.check_time.strftime('%H:%M:%S')
            }
            if include_reason:
                info["late_reason"] = item.late_reason
            data_list.append(info)
        return data_list