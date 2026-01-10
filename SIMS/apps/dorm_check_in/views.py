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
    """获取本次查寝需参与的学生（排除校外+请假学生）"""
    check_latest_dt, _, _ = get_check_latest_dt(check_config)

    # 子查询：获取需排除的请假学生ID（适配User的student_id为CharField）
    exclude_student_ids = LeaveRequest.objects.filter(
        status="approved",
        end_time__gt=check_latest_dt,  # 请假结束时间 > 查寝最晚时间
        start_time__lte=check_latest_dt  # 请假开始时间 ≤ 查寝最晚时间（避免无关请假）
    ).values_list("student_id", flat=True)

    # 筛选需参与查寝的学生
    # 关键修改：适配User模型的住宿字段（dorm_type + dormitory）
    valid_students = User.objects.filter(
        role="student",
        dorm_type="internal",  # 校内住宿
        dormitory__isnull=False  # 绑定了宿舍楼
    ).exclude(
        student_id__in=exclude_student_ids  # 修正：用student_id而非id匹配
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
        # 捕获JSON解析错误（解决参数格式错误返回异常的问题）
        try:
            request_data = request.data if isinstance(request.data, dict) else json.loads(request.body)
        except JSONDecodeError:
            return Response({"detail": "请求参数格式错误，请检查JSON格式是否正确"}, status=status.HTTP_400_BAD_REQUEST)

        # 权限校验1：判断是否登录
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录系统"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        # 权限校验2：判断身份是否合格
        if user.role != "student":
            return Response({"detail": "仅学生可打卡"}, status=status.HTTP_403_FORBIDDEN)

        # 参数获取&校验
        check_config_id = request_data.get("check_config_id")
        lat = request_data.get("lat")
        lng = request_data.get("lng")
        late_reason = request_data.get("late_reason", "").strip()  # 去除首尾空格
        material = request.FILES.get("material")

        if not all([check_config_id, lat, lng]):
            return Response({"detail": "查寝配置ID、纬度、经度为必填项"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_config_id = int(check_config_id)
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            return Response({"detail": "查寝配置ID为整数，经纬度为数字"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取查寝配置
        try:
            check_config = CheckConfig.objects.get(id=check_config_id, is_active=True)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在或未生效"}, status=status.HTTP_404_NOT_FOUND)

        # 时间校验
        now = timezone.localtime(timezone.now())  # 转换为本地时间（解决时区差8小时问题）
        check_latest_dt, normal_end_dt, normal_start_dt = get_check_latest_dt(check_config)

        # 校验1：未到打卡开始时间
        if now < normal_start_dt:
            return Response({
                "detail": f"打卡尚未开始（开始时间：{normal_start_dt.strftime('%Y-%m-%d %H:%M')}），无法打卡"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 校验2：超过打卡截止时间
        if now > check_latest_dt:
            return Response({
                "detail": f"已超过打卡截止时间（{check_latest_dt.strftime('%Y-%m-%d %H:%M')}），无法打卡"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 学生状态校验：校外住宿（适配User模型的dorm_type字段）
        if user.dorm_type == "external":
            return Response({"detail": "你属于校外住宿，无需参与本次查寝"}, status=status.HTTP_200_OK)

        # 学生状态校验：校内住宿但未绑定宿舍楼
        if user.dorm_type == "internal" and not user.dormitory:
            return Response({"detail": "你属于校内住宿，但未绑定宿舍楼，请联系管理员"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 学生状态校验：请假（结束时间>查寝最晚时间）
        # 修正：LeaveRequest的student_id匹配User的student_id（CharField）
        leave_records = LeaveRequest.objects.filter(
            student_id=user.student_id,
            status="approved",
            start_time__lte=check_latest_dt
        )
        for leave in leave_records:
            if leave.end_time > check_latest_dt:
                return Response(
                    {"detail": f"你请假至{leave.end_time.strftime('%Y-%m-%d %H:%M')}，晚于查寝截止时间，无需查寝"},
                    status=status.HTTP_200_OK)

        # 寝室校验（适配User模型的dormitory字段）
        dorm = user.dormitory
        if not dorm:
            return Response({"detail": "未绑定宿舍楼信息，无法打卡"}, status=status.HTTP_400_BAD_REQUEST)

        # 位置校验（需实现haversine函数，计算两点距离）
        try:
            from .utils import haversine
            # 修正：dormitory模型需有lng/lat字段，这里兼容字段名
            dist = haversine(lng, lat, float(dorm.longitude), float(dorm.latitude))
        except AttributeError as e:
            return Response({"detail": f"宿舍楼缺少经纬度信息：{str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"detail": f"位置计算失败：{str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if dist > check_config.valid_range:
            return Response({"detail": f"打卡位置超出宿舍楼{check_config.valid_range}米范围，无法打卡"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 打卡状态判定
        check_status = "normal"
        if check_config.late_end:
            check_status = "normal" if now <= normal_end_dt else "late"
            # 晚归理由校验（解决JSON解析错误问题，先校验再返回）
            if check_status == "late" and not late_reason:
                return Response({"detail": "晚归打卡必须填写晚归理由"}, status=status.HTTP_400_BAD_REQUEST)
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
            }, status=status.HTTP_200_OK)

        # 创建打卡记录
        # 修正：学生姓名优先取get_full_name()，无则用username（适配User模型）
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
            material=material,
            msg=f"{'正常' if check_status == 'normal' else '晚归'}打卡成功"
        )

        # 响应
        return Response({
            "is_success": True,
            "check_status": attendance.get_check_status_display(),
            "student_name": attendance.student_name,
            "student_id": user.student_id,  # 补充返回学号/工号
            "distance": round(dist, 2),
            "check_time": attendance.check_time.strftime('%Y-%m-%d %H:%M:%S'),
            "msg": attendance.msg
        }, status=status.HTTP_201_CREATED)


# ---------------------- 教师端：实时统计接口 ----------------------
class AttendanceStatisticsView(APIView):
    """教师查看单天查寝的分阶段统计"""

    def get(self, request):
        # 权限校验1：判断是否登录
        if not request.user.is_authenticated:
            return Response({"detail": "请先登录系统"}, status=status.HTTP_401_UNAUTHORIZED)

        # 权限校验2：判断身份是否合格
        if request.user.role not in ["teacher",  "admin"]:
            return Response({"detail": "仅教师/管理员可查看统计数据"}, status=status.HTTP_403_FORBIDDEN)

        # 参数获取
        check_config_id = request.query_params.get("check_config_id")
        if not check_config_id:
            return Response({"detail": "查寝配置ID为必填项"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取查寝配置
        try:
            check_config = CheckConfig.objects.get(id=check_config_id)
        except CheckConfig.DoesNotExist:
            return Response({"detail": "查寝配置不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 基础数据：需参与查寝的学生
        valid_students, check_latest_dt = get_valid_students(check_config)
        total_students = valid_students.count()
        # 已打卡学生
        checked_students = Attendance.objects.filter(check_config=check_config)
        # 修正：获取student_id（CharField）而非id
        checked_student_ids = checked_students.values_list("student__student_id", flat=True)

        # 阶段判定
        now = timezone.localtime(timezone.now())  # 转换为本地时间（解决时区差8小时问题）
        _, normal_end_dt, _ = get_check_latest_dt(check_config)
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
                    "student_id": item.student.student_id,  # 学号/工号（CharField）
                    "student_name": item.student_name,
                    "college": item.student.college,  # 补充学院信息
                    "major": item.student.major,  # 补充专业信息
                    "class_name": item.student.class_name,  # 补充班级信息
                    "dorm_building": item.dorm.name,  # 宿舍楼名称
                    "dorm_room": item.student.address,  # 寝室号（User的address字段）
                    "check_time": item.check_time.strftime('%Y-%m-%d %H:%M')
                } for item in checked_students
            ]
            statistics["unchecked_count"] = total_students - statistics["checked_count"]
            statistics["unchecked_list"] = [
                {
                    "student_id": user.student_id,
                    "student_name": user.get_full_name() or user.username,
                    "college": user.college,
                    "major": user.major,
                    "class_name": user.class_name,
                    "dorm_building": user.dormitory.name if user.dormitory else "",
                    "dorm_room": user.address
                } for user in valid_students.exclude(student_id__in=checked_student_ids)
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
                    "college": item.student.college,
                    "major": item.student.major,
                    "class_name": item.student.class_name,
                    "dorm_building": item.dorm.name,
                    "dorm_room": item.student.address,
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
                    "college": item.student.college,
                    "major": item.student.major,
                    "class_name": item.student.class_name,
                    "dorm_building": item.dorm.name,
                    "dorm_room": item.student.address,
                    "check_time": item.check_time.strftime('%Y-%m-%d %H:%M'),
                    "late_reason": item.late_reason
                } for item in late_students
            ]
            # 未归寝
            statistics["absent_count"] = total_students - (statistics["normal_count"] + statistics["late_count"])
            statistics["absent_list"] = [
                {
                    "student_id": user.student_id,
                    "student_name": user.get_full_name() or user.username,
                    "college": user.college,
                    "major": user.major,
                    "class_name": user.class_name,
                    "dorm_building": user.dormitory.name if user.dormitory else "",
                    "dorm_room": user.address
                } for user in valid_students.exclude(student_id__in=checked_student_ids)
            ]

        return Response(statistics, status=status.HTTP_200_OK)