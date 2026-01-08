from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 把关键信息写入 Token 载荷 (Payload)
        token['role'] = user.role
        token['username'] = user.username
        token['student_id'] = user.student_id
        token['college'] = user.college
        return token

    def validate(self, attrs):
        # 验证密码并生成 access/refresh token
        data = super().validate(attrs)

        # 在登录响应的 JSON 中添加用户信息
        data['id'] = self.user.id
        data['username'] = self.user.username
        data['role'] = self.user.role
        data['student_id'] = self.user.student_id
        data['college'] = self.user.college
        data['major'] = self.user.major
        data['grade'] = self.user.grade
        data['class_name'] = self.user.class_name
        data['phone'] = self.user.phone        
        data['birthday'] = self.user.birthday  
        # --------------------------

        # 获取培养层次的中文显示名 (如 "本科生")
        data['education_level'] = self.user.get_education_level_display() 
        data['gender_display'] = self.user.get_gender_display()  
        
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'role', 'student_id',
            'college', 'major', 'grade', 'class_name',
            'education_level', 'gender', 'phone', 'birthday'
        )
        extra_kwargs = {
            'password': {'write_only': True} # 密码不参与序列化输出
        }

    def create(self, validated_data):
        # 使用 create_user 以确保密码被哈希加密
        user = User.objects.create_user(**validated_data)
        return user