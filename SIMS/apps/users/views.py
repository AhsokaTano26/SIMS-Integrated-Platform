from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .serializers import MyTokenObtainPairSerializer

# 使用自定义的序列化器
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # 允许任何人注册 (POST)，但只有管理员可以查看/修改所有用户列表
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), permissions.IsAdminUser()] # 仅限管理员

    # 管理员重置密码接口
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """
        路径: /api/auth/users/{id}/reset-password/
        """
        # 1. 权限校验：仅限管理员
        if request.user.role != 'admin':
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()

        # 2. 设置新密码
        new_pwd = "password123"  # 你也可以从 request.data 获取自定义密码
        user.set_password(new_pwd)
        user.save()

        return Response({
            "detail": f"用户 {user.username} 的密码已重置为: {new_pwd}",
            "username": user.username
        }, status=status.HTTP_200_OK)