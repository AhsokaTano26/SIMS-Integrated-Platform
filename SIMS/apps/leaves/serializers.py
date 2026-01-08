from rest_framework import serializers
from .models import LeaveRequest


class LeaveSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.username')

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ('student', 'created_at')