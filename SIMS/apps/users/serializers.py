from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 把角色信息写入 Token (解析 Token 时可用)
        token['role'] = user.role
        token['username'] = user.username
        return token

    # 修改返回的 JSON 数据结构
    def validate(self, attrs):
        data = super().validate(attrs)

        # 在响应体中直接添加用户信息，方便前端存入 Pinia/Vuex
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['id'] = self.user.id
        return data