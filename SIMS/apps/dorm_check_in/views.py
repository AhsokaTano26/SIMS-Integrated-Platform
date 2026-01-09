# apps/attendance/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Attendance, CheckConfig
from leaves.models import LeaveRequest
from users.models import User


# ---------------------- 工具函数：通用逻辑抽离 ----------------------
def get_check_latest_dt(check_config):
    """计算查寝的最晚截止时间（兼容跨天）"""
    check_date = check_config.check_date
    # 拼接正常结束时间
    normal_end_dt = timezone.make_aware(datetime.combine(check_date, check_config.normal_end))
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
    return check_latest_dt, normal_end_dt


def get_valid_students(check_config):
    """获取本次查寝需参与的学生（排除校外+请假学生）"""
    check_latest_dt, _ = get_check_latest_dt(check_config)

    # 子查询：获取需排除的请假学生ID
    exclude_student_ids = LeaveRequest.objects.filter(
        status="approved",
        end_datetime__gt=check_latest_dt,  # 请假结束时间 > 查寝最晚时间
        start_datetime__lte=check_latest_dt  # 请假开始时间 ≤ 查寝最晚时间（避免无关请假）
    ).values_list("student_id", flat=True)

    # 筛选需参与查寝的学生
    valid_students = User.objects.filter(
        role="student",
        dorm__isnull=False,
        dorm__is_offcampus=False
    ).exclude(
        id__in=exclude_student_ids
    )
    return valid_students, check_latest_dt


# ---------------------- 教师端：查寝配置接口 ----------------------
class CheckConfigView(APIView):
    """创建/修改单天查寝配置"""

    def post(self, request):
        # 权限校验
        if request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "仅教师/管理员可配置查寝规则"}, status=403)

        # 参数校验
        params = request.data
        required_fields = ["config_name", "check_date", "normal_start", "normal_end"]
        for field in required_fields:
            if not params.get(field):
                return Response({"detail": f"{field}为必填项"}, status=400)

        # 时间转换
        try:
            check_date = datetime.strptime(params.get("check_date"), "%Y-%m-%d").date()
            normal_start = datetime.strptime(params.get("normal_start"), "%H:%M").time()
            normal_end = datetime.strptime(params.get("normal_end"), "%H:%M").time()
            late_end = datetime.strptime(params.get("late_end"), "%H:%M").time() if params.get("late_end") else None
        except ValueError:
            return Response({"detail": "日期格式为YYYY-MM-DD，时间格式为HH:MM"}, status=400)

        # 创建配置
        config = CheckConfig.objects.create(
            config_name=params.get("config_name"),
            check_date=check_date,
            normal_start=normal_start,
            normal_end=normal_end,
            late_end=late_end,
            valid_range=int(params.get("valid_range", 500)),
            need_material=params.get("need_material", False),
            notify_normal_after_normal_end=params.get("notify_normal_after_normal_end", True),
            notify_late_after_late_end=params.get("notify_late_after_late_end", True) if late_end else False,
            is_active=params.get("is_active", True),
            created_by=request.user
        )

        # 响应
        response_data = {
            "id": config.id,
            "msg": "查寝配置创建成功",
            "config": {
                "name": config.config_name,
                "date": config.check_date,
                "normal_time": f"{config.normal_start}-{config.normal_end}",
                "late_time": config.late_end if config.late_end else "无晚归时段",
                "range": config.valid_range
            }
        }
        return Response(response_data, status=201)


# ---------------------- 学生端：打卡接口 ----------------------
class AttendanceView(APIView):
    """学生查寝打卡"""

    def post(self, request):
        user = request.user
        # 权限校验
        if user.role != "student":
            return Response({"detail": "仅学生可打卡"}, status=403)

        # 参数获取&校验
        check_config_id = request.data.get("check_config_id")
        lat = request.data.get("lat")
        lng = request.data.get("lng")
        late_reason = request.data.get("late_reason", "")
        material = request.FILES.get("material")

        if not all([check_config_id, lat, lng]):
            return Response({"detail": "查寝配置ID、纬度、经度为必填项"}, status=400)

        try:
            check_config_id = int(check_config_id)
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response({"detail": "查寝配置ID为整数，经纬度为数字"}, status=400)

        # 获取查寝配置
        try:
            check_config = CheckConfig.objects.get(id=check_config_id, is_active=True)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在或未生效"}, status=404)

        # 时间校验
        now = timezone.now()
        check_latest_dt, normal_end_dt = get_check_latest_dt(check_config)
        if now > check_latest_dt:
            return Response({"detail": f"已超过打卡截止时间（{check_latest_dt.strftime('%Y-%m-%d %H:%M')}），无法打卡"},
                            status=400)

        # 学生状态校验：校外住宿
        if user.dorm and user.dorm.is_offcampus:
            return Response({"detail": "你属于校外住宿，无需参与本次查寝"}, status=200)

        # 学生状态校验：请假（结束时间>查寝最晚时间）
        leave_records = LeaveRequest.objects.filter(
            student_id=user.student_id,
            status="approved",
            start_datetime__lte=check_latest_dt
        )
        for leave in leave_records:
            if leave.end_datetime > check_latest_dt:
                return Response(
                    {"detail": f"你请假至{leave.end_datetime.strftime('%Y-%m-%d %H:%M')}，晚于查寝截止时间，无需查寝"},
                    status=200)

        # 寝室校验
        if not user.dorm:
            return Response({"detail": "未绑定寝室信息，无法打卡"}, status=400)
        dorm = user.dorm

        # 位置校验（需实现haversine函数，计算两点距离）
        try:
            from .utils import haversine
            dist = haversine(lng, lat, float(dorm.lng), float(dorm.lat))  # 假设dorm有lng/lat字段
        except Exception as e:
            return Response({"detail": f"位置计算失败：{str(e)}"}, status=500)

        if dist > check_config.valid_range:
            return Response({"detail": f"打卡位置超出寝室{check_config.valid_range}米范围，无法打卡"}, status=400)

        # 打卡状态判定
        if check_config.late_end:
            check_status = "normal" if now <= normal_end_dt else "late"
            if check_status == "late" and not late_reason:
                return Response({"detail": "晚归打卡必须填写晚归理由"}, status=400)
        else:
            check_status = "normal"

        # 重复打卡校验（已有记录则拒绝）
        existing_attendance = Attendance.objects.filter(
            student=user,
            check_config=check_config
        ).first()
        if existing_attendance:
            return Response({
                "is_success": False,
                "msg": "你已完成本次查寝打卡，不可重复打卡",
                "existing_check_time": existing_attendance.check_time.strftime('%Y-%m-%d %H:%M:%S')
            }, status=200)

        # 创建打卡记录
        attendance = Attendance.objects.create(
            student=user,
            student_name=user.real_name,
            dorm=dorm,
            check_config=check_config,
            lat=lat,
            lng=lng,
            distance=dist,
            check_time=now,
            check_status=check_status,
            late_reason=late_reason,
            material=material,
            msg=f"{'正常' if check_status == 'normal' else '晚归'}打卡成功"
        )

        # 响应
        return Response({
            "is_success": True,
            "check_status": attendance.get_check_status_display(),
            "student_name": attendance.student_name,
            "distance": round(dist, 2),
            "check_time": attendance.check_time.strftime('%Y-%m-%d %H:%M:%S'),
            "msg": attendance.msg
        }, status=201)


# ---------------------- 教师端：实时统计接口 ----------------------
class AttendanceStatisticsView(APIView):
    """教师查看单天查寝的分阶段统计"""

    def get(self, request):
        # 权限校验
        if request.user.role not in ["teacher", "admin"]:
            return Response({"detail": "权限不足"}, status=403)

        # 参数获取
        check_config_id = request.query_params.get("check_config_id")
        if not check_config_id:
            return Response({"detail": "查寝配置ID为必填项"}, status=400)

        # 获取查寝配置
        try:
            check_config = CheckConfig.objects.get(id=check_config_id)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在"}, status=404)

        # 基础数据：需参与查寝的学生
        valid_students, check_latest_dt = get_valid_students(check_config)
        total_students = valid_students.count()
        # 已打卡学生
        checked_students = Attendance.objects.filter(check_config=check_config)
        checked_student_ids = checked_students.values_list("student_id", flat=True)

        # 阶段判定
        now = timezone.now()
        _, normal_end_dt = get_check_latest_dt(check_config)
        stage = 1 if now < normal_end_dt else 2
        stage_desc = "正常签到中" if stage == 1 else "正常签到已结束"

        # 统计数据初始化
        statistics = {
            "check_config_id": check_config.id,
            "check_date": check_config.check_date,
            "stage": stage,
            "stage_desc": stage_desc,
            "total_students": total_students,
            "check_latest_time": check_latest_dt.strftime('%Y-%m-%d %H:%M')
        }

        # 阶段1：正常签到结束前 → 仅显示已归/未归
        if stage == 1:
            statistics["checked_count"] = checked_students.count()
            statistics["checked_list"] = [
                {
                    "student_id": item.student.student_id,
                    "student_name": item.student_name,
                    "dorm": item.dorm.dorm_num,
                    "check_time": item.check_time.strftime('%Y-%m-%d %H:%M')
                } for item in checked_students
            ]
            statistics["unchecked_count"] = total_students - statistics["checked_count"]
            statistics["unchecked_list"] = [
                {
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "dorm": user.dorm.dorm_num
                } for user in valid_students.exclude(id__in=checked_student_ids)
            ]

        # 阶段2：正常签到结束后 → 显示已归/晚归/未归
        else:
            # 正常打卡
            normal_students = checked_students.filter(check_status="normal")
            statistics["normal_count"] = normal_students.count()
            statistics["normal_list"] = [
                {
                    "student_id": item.student.student_id,
                    "student_name": item.student_name,
                    "dorm": item.dorm.dorm_num,
                    "check_time": item.check_time.strftime('%Y-%m-%d %H:%M')
                } for item in normal_students
            ]
            # 晚归打卡
            late_students = checked_students.filter(check_status="late")
            statistics["late_count"] = late_students.count()
            statistics["late_list"] = [
                {
                    "student_id": item.student.student_id,
                    "student_name": item.student_name,
                    "dorm": item.dorm.dorm_num,
                    "check_time": item.check_time.strftime('%Y-%m-%d %H:%M'),
                    "late_reason": item.late_reason
                } for item in late_students
            ]
            # 未归寝
            statistics["absent_count"] = total_students - (statistics["normal_count"] + statistics["late_count"])
            statistics["absent_list"] = [
                {
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "dorm": user.dorm.dorm_num
                } for user in valid_students.exclude(id__in=checked_student_ids)
            ]

        return Response(statistics, status=200)