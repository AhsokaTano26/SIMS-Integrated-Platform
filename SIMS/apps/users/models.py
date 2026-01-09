from django.db import models
from django.contrib.auth.models import AbstractUser
import os
import hashlib

def user_avatar_path(instance, filename):
    """
    自定义上传路径及文件名
    通过 用户ID + 原始文件名 进行 SHA256 哈希，确保文件名唯一且不可预测
    """
    # 获取文件后缀名 (例如 .jpg)
    ext = filename.split('.')[-1]
    # 构建哈希内容
    hash_str = f"user_{instance.id}_{filename}"
    file_hash = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
    # 返回存储路径：avatars/哈希值.后缀
    return os.path.join('avatars', f"{file_hash}.{ext}")

#增加住宿表
class Dormitory(models.Model):
    # Django 默认会生成自增的 id 字段，我们可以直接将其视为“编号”
    # 如果你想显式定义，可以使用：id = models.AutoField(primary_key=True)
    
    name = models.CharField(max_length=100, unique=True, verbose_name="宿舍楼名称")
    
    # 地理坐标（用于定位打卡）
    latitude = models.FloatField(verbose_name="中心点纬度")
    longitude = models.FloatField(verbose_name="中心点经度")
    
    # 考勤范围
    radius = models.IntegerField(default=200, verbose_name="考勤半径(米)")

    class Meta:
        verbose_name = '宿舍楼'
        verbose_name_plural = '宿舍楼列表'

    def __str__(self):
        # 在管理后台显示为：[编号] 名称
        return f"[{self.id}] {self.name}"


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

    # 5. 住宿信息
    dorm_type = models.CharField(
        max_length=10, 
        choices=DORM_TYPE_CHOICES, 
        verbose_name="住宿标识"
    )
    
    # 逻辑必填：如果是校内，前端必须传这个 ID
    dormitory = models.ForeignKey(
        'Dormitory', 
        on_delete=models.PROTECT, 
        null=True, # 数据库允许空，由业务逻辑校验必填
        blank=True, 
        verbose_name="所属宿舍楼"
    )
    
    # 通用详细地址：校内填“302”，校外填“XX路XX号”
    address = models.CharField(
        max_length=255, 
        verbose_name="详细地址", 
        help_text="校内：仅填寝室号（如302）；校外：填完整详细地址"
    )
    # 6. 头像字段
    avatar = models.ImageField(
        upload_to=user_avatar_path, 
        null=True, 
        blank=True, 
        verbose_name="用户头像"
    )

    # 动态获取头像的逻辑
    @property
    def avatar_url(self):
        """
        如果用户上传了头像，返回头像路径；
        如果没有上传，根据性别返回预设的默认头像路径。
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        
        # 默认头像逻辑：假设你在 media/defaults/ 下放了对应的图片
        if self.gender == 'male':
            return '/media/defaults/male.png'
        elif self.gender == 'female':
            return '/media/defaults/female.png'
        else:
            return '/media/defaults/unknown.png'

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.student_id}"