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
        # 允许任何人访问的操作：注册 (create)、身份核验、自主重置密码
        allow_any_actions = ['create', 'verify_user_info', 'self_reset_password']
        
        if self.action in allow_any_actions:
            return [permissions.AllowAny()]
            
        # 其他操作（如删除用户、列表查看、管理员重置）：仅限已登录的管理员
        return [permissions.IsAuthenticated(), permissions.IsAdminUser()]

    # --- 新增：忘记密码的第一步，核验身份 ---
    @action(detail=False, methods=['post'], url_path='verify-user')
    def verify_user_info(self, request):
        """
        路径: /api/auth/users/verify-user/
        """
        student_id = request.data.get('student_id')
        username = request.data.get('username')
        
        # 在数据库中查找匹配学号和姓名的用户
        user = User.objects.filter(student_id=student_id, username=username).first()
        
        if user:
            return Response({"detail": "核验成功", "id": user.id}, status=status.HTTP_200_OK)
        return Response({"detail": "学号与姓名不匹配"}, status=status.HTTP_400_BAD_REQUEST)

    # --- 新增：忘记密码的第二步，提交新密码 ---
    @action(detail=False, methods=['post'], url_path='self-reset-password')
    def self_reset_password(self, request):
        """
        路径: /api/auth/users/self-reset-password/
        """
        student_id = request.data.get('student_id')
        username = request.data.get('username')
        new_password = request.data.get('new_password')

        # 安全起见，再次核验身份
        user = User.objects.filter(student_id=student_id, username=username).first()
        
        if user:
            user.set_password(new_password)
            user.save()
            return Response({"detail": "密码重置成功"}, status=status.HTTP_200_OK)
        return Response({"detail": "重置失败，身份信息已失效"}, status=status.HTTP_400_BAD_REQUEST)

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