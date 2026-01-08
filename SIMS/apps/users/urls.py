from django.urls import path
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # 登录接口：获取 Token
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 刷新接口：Token 过期后换新的
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]