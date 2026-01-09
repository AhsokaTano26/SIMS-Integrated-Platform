from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('counselor','辅导员'),
        ('admin', '管理员'),
    )
    # 住宿类型标识
    DORM_TYPE_CHOICES = (
        ('internal', '校内住宿'),
        ('external', '校外住宿'),
    )
    # 培养层次
    LEVEL_CHOICES = (
        ('undergraduate', '本科生'),
        ('master', '硕士研究生'),
        ('doctor', '博士研究生'),
    )
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女'),
        ('unknown', '保密'),
    )
    # 1. 基础扩展字段
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="角色")
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="学号/工号")
    
    # 2. 组织架构字段 (仿钉钉/学校架构)
    college = models.CharField(max_length=100, blank=True, verbose_name="学院")
    major = models.CharField(max_length=100, blank=True, verbose_name="专业")
    grade = models.CharField(max_length=10, blank=True, verbose_name="年级", help_text="如：2023级")
    class_name = models.CharField(max_length=50, blank=True, verbose_name="班级")
    
    
    # 3. 培养信息
    education_level = models.CharField(
        max_length=20, 
        choices=LEVEL_CHOICES, 
        default='undergraduate', 
        verbose_name="培养层次"
    )
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        default='unknown', 
        verbose_name="性别"
    )

    # 4. 个人隐私信息
    phone = models.CharField(max_length=11, blank=True, verbose_name="联系电话")
    birthday = models.DateField(null=True, blank=True, verbose_name="出生日期")

    # 5. 住宿信息扩展
    dorm_type = models.CharField(
        max_length=10, 
        choices=DORM_TYPE_CHOICES, 
        default='internal', 
        verbose_name="住宿标识"
    )
    address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="住宿详细地址",
        help_text="校内：宿舍号（如8舍302）；校外：具体街道及门牌号"
    )
    

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.student_id}"