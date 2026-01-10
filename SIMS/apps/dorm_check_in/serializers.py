from rest_framework import serializers
from .models import CheckConfig

class CheckConfigListSerializer(serializers.ModelSerializer):
    # 将模型中的 @property 映射为接口字段
    status = serializers.ReadOnlyField(source='current_status')
    status_desc = serializers.ReadOnlyField(source='status_display')

    class Meta:
        model = CheckConfig
        fields = [
            'id', 'config_name', 'check_date',
            'normal_start', 'normal_end', 'late_end',
            'status', 'status_desc'
        ]