from rest_framework import serializers
from .models import LeaveRequest


class LeaveSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    student_name = serializers.ReadOnlyField(source='student.username')
    student_id_display = serializers.ReadOnlyField(source='student.student_id')

    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'student',
            'student_id_display',
            'student_name',
            'reason',
            'start_time',
            'end_time',
            'status',
            'comment',
            'created_at',
            'report_back_time',
            'is_overdue'
        ]
        # student 必须设为只读，防止学生发 POST 时伪造他人 ID
        read_only_fields = ('student', 'created_at', 'status', 'comment')