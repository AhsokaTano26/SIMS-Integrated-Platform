from django.urls import path
from . import views

urlpatterns = [
    # 查寝配置
    path("config/", views.CheckConfigView.as_view(), name="check-config"),
    # 学生打卡
    path("attendance/", views.AttendanceView.as_view(), name="attendance"),
    # 统计查询
    path("statistics/", views.AttendanceStatisticsView.as_view(), name="attendance-statistics"),
]