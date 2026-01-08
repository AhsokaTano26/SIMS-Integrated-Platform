from .models import Attendance
from .utils import haversine
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from leaves.models import LeaveRequest
from attendance.models import Attendance
from users.models import User


class AttendanceView(APIView):
    def post(self, request):
        user = request.user
        lat = float(request.data.get('lat'))
        lng = float(request.data.get('lng'))

        # 假设宿舍坐标 (例如：北京某处)
        DORM_LAT, DORM_LNG = 29.599517, 106.290993

        dist = haversine(lng, lat, DORM_LNG, DORM_LAT)
        is_normal = dist <= 1000  # 500米以内算正常

        msg = "打卡成功" if is_normal else f"异常：超出范围{int(dist)}米"

        Attendance.objects.create(
            student=user, lat=lat, lng=lng,
            distance=dist, is_normal=is_normal, msg=msg
        )

        return Response({
            "is_normal": is_normal,
            "distance": round(dist, 2),
            "msg": msg
        })

    def get(self, request):
        if request.user.role != 'teacher':
            return Response({"detail": "权限不足"}, status=403)

        # 获取最近 24 小时内的异常记录
        from django.utils import timezone
        last_24h = timezone.now() - timezone.timedelta(hours=24)

        # 筛选异常打卡
        abnormal_list = Attendance.objects.filter(
            is_normal=False,
            created_at__gte=last_24h
        ).order_by('-created_at')

        # 构造前端需要的数据结构
        data = [{
            "id": item.id,
            "student": item.student.username,
            "distance": round(item.distance, 1),
            "time": item.created_at.strftime('%m-%d %H:%M'),
            "msg": item.msg
        } for item in abnormal_list]

        return Response(data)

class StatisticsView(APIView):
    # 仅限教师和管理员查看
    def get(self, request):
        today = timezone.now().date()
        last_week = today - timedelta(days=7)

        # 1. 学院打卡率 (热力图/柱状图数据)
        colleges = User.objects.filter(role='student').values('college').annotate(
            total=Count('id'),
            present=Count('attendance', filter=Q(attendance__created_at__date=today))
        )
        college_data = [
            {"name": c['college'], "value": round((c['present']/c['total'])*100, 1) if c['total'] > 0 else 0}
            for c in colleges
        ]

        # 2. 异常趋势图 (过去7天)
        trend_data = []
        for i in range(7):
            date = last_week + timedelta(days=i)
            count = Attendance.objects.filter(created_at__date=date, is_normal=False).count()
            trend_data.append({"date": date.strftime('%m-%d'), "count": count})

        # 3. 请假原因分布 (饼图)
        leave_reasons = LeaveRequest.objects.values('reason').annotate(count=Count('id'))
        # 简单分类处理（实际开发中建议数据库reason字段设为选择项）
        reason_data = [{"name": r['reason'][:4], "value": r['count']} for r in leave_reasons]

        return Response({
            "college_rate": college_data,
            "trend": trend_data,
            "reasons": reason_data
        })