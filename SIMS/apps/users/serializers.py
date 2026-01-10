from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from users.models import Dormitory

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 显式添加 student_id 字段，让后端允许接收这个键
        self.fields['student_id'] = serializers.CharField()
        # 2. 不要 del self.fields['username']！！
        # 而是将其设为非必填，防止前端没传时直接报 400
        self.fields['username'].required = False

    def validate(self, attrs):
        student_id = attrs.get('student_id')
        password = attrs.get('password')

        # 3. 通过学号反查原生的“用户名”
        try:
            # 假设你的 User Model 里确实有 student_id 字段
            user_obj = User.objects.get(student_id=student_id)
            # 【重点】手动补上 username 键，这样 super().validate 就不会报 KeyError 了
            attrs['username'] = user_obj.username 
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "学号不存在"})

        # 4. 调用父类方法，它会拿着查出来的原生 username 去比对密码
        # 此时 attrs 已经完整，KeyError 消失
        data = super().validate(attrs)

        # 添加自定义返回字段
        data['id'] = self.user.id
        data['role'] = self.user.role
        data['student_id'] = self.user.student_id
        data['username'] = self.user.username  
        data['college'] = self.user.college
        data['major'] = self.user.major
        data['grade'] = self.user.grade
        data['class_name'] = self.user.class_name
        data['phone'] = self.user.phone
        
        # 住宿信息
        data['dorm_type'] = self.user.dorm_type
        data['dormitory'] = self.user.dormitory.id if self.user.dormitory else None
        data['dormitory_name'] = self.user.dormitory.name if self.user.dormitory else "校外"
        data['address'] = self.user.address
        
        # 其他
        data['avatar'] = self.user.avatar_url
        data['education_level'] = self.user.get_education_level_display() 
        data['gender_display'] = self.user.get_gender_display()
        data['email'] = self.user.email
        
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
            'dorm_type','address','dormitory','email'
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