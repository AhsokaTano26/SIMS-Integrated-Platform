from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from users.models import Dormitory

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

        # --- 新增：住宿信息返回 ---
        data['dorm_type'] = self.user.dorm_type
        data['dormitory'] = self.user.dormitory.id if self.user.dormitory else None
        data['dormitory_name'] = self.user.dormitory.name if self.user.dormitory else "校外"
        data['address'] = self.user.address

        # --- 新增：头像 URL 返回 ---
        # 对应你在 model 中定义的 @property avatar_url
        data['avatar'] = self.user.avatar_url

        # 获取培养层次的中文显示名 (如 "本科生")
        data['education_level'] = self.user.get_education_level_display() 
        data['gender_display'] = self.user.get_gender_display()  
        
        return data

class UserSerializer(serializers.ModelSerializer):
    # 新增：定义一个只读字段，用来获取 model 里的 avatar_url 属性
    avatar_url = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'role', 'student_id',
            'college', 'major', 'grade', 'class_name',
            'education_level', 'gender', 'phone', 'birthday','avatar','avatar_url',
            'dorm_type', 'address'
        )
        extra_kwargs = {
            'password': {'write_only': True}, # 密码不参与序列化输出
            'avatar': {'write_only': True}, # 上传时使用，不返回在 JSON 列表里
        }
    
    def validate(self, data):
        """
        在注册/更新时执行必填逻辑校验
        """
        dorm_type = data.get('dorm_type')
        dormitory = data.get('dormitory')
        address = data.get('address')

        if dorm_type == 'internal':
            if not dormitory:
                raise serializers.ValidationError({"dormitory": "校内住宿必须选择宿舍楼"})
            if not address:
                raise serializers.ValidationError({"address": "校内住宿必须填写寝室号"})
        
        elif dorm_type == 'external':
            if not address:
                raise serializers.ValidationError({"address": "校外住宿必须填写详细住址"})
            # 校外住宿强制将楼栋设为空
            data['dormitory'] = None
            
        return data

    def create(self, validated_data):
        # 使用 create_user 以确保密码被哈希加密
        user = User.objects.create_user(**validated_data)
        return user

# 完整版（老师和管理员用）
class DormitorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = '__all__'

# 简化版（学生注册或查看用）
class DormitorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = ['id', 'name'] # 仅暴露 ID 和 名称，隐藏坐标等敏感信息