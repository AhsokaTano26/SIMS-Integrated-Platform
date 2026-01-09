from django.db import models
from django.conf import settings

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', '待审批'),
        ('approved', '已准假'),
        ('rejected', '已驳回'),
        ('completed', '已销假'),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaves')
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    reason = models.TextField(verbose_name="请假原因")
    evidence = models.ImageField(upload_to='leaves/%Y/%m/', null=True, blank=True, verbose_name="证明材料")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    leave_for = models.TextField(verbose_name="请假去向")
    def __str__(self):
        return f"{self.student.username} - {self.get_status_display()}"