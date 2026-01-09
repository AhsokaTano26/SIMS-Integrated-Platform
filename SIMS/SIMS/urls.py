"""
URL configuration for SIMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from leaves.views import LeaveViewSet
from attendance.views import AttendanceView, StatisticsView
from dorm_check_in.views import CheckConfigView, AttendanceView, AttendanceStatisticsView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'leaves', LeaveViewSet, basename='leave')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/attendance/', AttendanceView.as_view()),
    path('api/attendance/alerts/', AttendanceView.as_view()),
    path('api/', include(router.urls)),
    path('api/statistics/', StatisticsView.as_view()),
    path('api/dorm_check/', include('dorm_check_in.urls')),
]
# 仅在开发模式下使用 Django 托管媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)