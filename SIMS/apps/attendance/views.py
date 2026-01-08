from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Attendance
from .utils import haversine


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