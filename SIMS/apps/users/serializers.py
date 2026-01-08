from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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