from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '辅导员'),
        ('admin', '管理员'),
    )
    # 扩展字段
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    class_name = models.CharField(max_length=50, blank=True, verbose_name="班级")
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="学号/工号")

    # 可以在这里加一个头像字段
    # avatar = models.ImageField(upload_to='avatars/', null=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"