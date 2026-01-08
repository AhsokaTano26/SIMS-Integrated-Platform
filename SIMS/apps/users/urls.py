from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MyTokenObtainPairView

router = DefaultRouter()
# 注意：这里注册为空字符串 ''，因为在总路由中已经前缀了 'users/'
# 这样访问路径就是：/api/auth/users/
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    # 登录接口：/api/auth/login/
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 用户管理接口：/api/auth/users/ (由 router 自动生成)
    path('users/', include(router.urls)),
]