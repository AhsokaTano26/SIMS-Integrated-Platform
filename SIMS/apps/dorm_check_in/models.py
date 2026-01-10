from django.db import models
from django.contrib.auth import get_user_model
from datetime import time
from users.models import Dormitory

User = get_user_model()

from django.db import models
from datetime import datetime, timedelta, time
from django.utils import timezone
from users.models import User  # 假设你的 User 模型路径


class CheckConfig(models.Model):
    """查寝配置表（单天查寝）"""
    config_name = models.CharField(max_length=100, verbose_name="查寝配置名称")
    check_date = models.DateField(verbose_name="查寝日期")

    # 输入字段
    normal_start = models.TimeField(verbose_name="正常签到开始时间")
    normal_duration = models.IntegerField(verbose_name="正常打卡时长（分钟）")
    late_duration = models.IntegerField(default=0, verbose_name="晚归打卡时长（分钟）")

    # 自动计算的存储字段（用于数据库高效查询）
    normal_end = models.TimeField(verbose_name="正常签到结束时间", editable=False, null=True)
    late_end = models.TimeField(null=True, blank=True, verbose_name="晚归截止时间", editable=False)

    # 其他配置
    valid_range = models.IntegerField(default=500, verbose_name="打卡有效范围（米）")
    need_material = models.BooleanField(default=False, verbose_name="是否需要上传证明材料")
    notify_normal_after_normal_end = models.BooleanField(default=True, verbose_name="正常结束后是否通知")
    notify_late_after_late_end = models.BooleanField(default=False, verbose_name="晚归结束后是否通知")
    is_active = models.BooleanField(default=True, verbose_name="是否生效")

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_check_configs",
                                   verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "查寝配置"
        verbose_name_plural = "查寝配置"

    def save(self, *args, **kwargs):
        """
        重写 save 方法，在保存到数据库前自动根据时长计算结束时间点
        """
        # 将 date 和 time 拼接成 datetime 进行计算
        start_dt = datetime.combine(self.check_date, self.normal_start)

        # 1. 计算正常结束时间
        normal_end_dt = start_dt + timedelta(minutes=self.normal_duration)
        self.normal_end = normal_end_dt.time()

        # 2. 计算晚归截止时间
        if self.late_duration > 0:
            late_end_dt = normal_end_dt + timedelta(minutes=self.late_duration)
            self.late_end = late_end_dt.time()
        else:
            self.late_end = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.config_name}（{self.check_date} {self.normal_start}开始）"



class Attendance(models.Model):
    """打卡记录表"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendances", verbose_name="学生")
    student_name = models.CharField(max_length=50, verbose_name="学生姓名")  # 冗余存储，提升查询性能
    dorm = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name="attendances", verbose_name="寝室")
    check_config = models.ForeignKey(CheckConfig, on_delete=models.CASCADE, related_name="attendances", verbose_name="查寝配置")
    lat = models.FloatField(verbose_name="打卡纬度")
    lng = models.FloatField(verbose_name="打卡经度")
    distance = models.FloatField(verbose_name="与寝室的距离（米）")
    check_time = models.DateTimeField(verbose_name="打卡时间")
    check_status = models.CharField(max_length=10, choices=[("normal", "正常"), ("late", "晚归")], verbose_name="打卡状态")
    late_reason = models.TextField(blank=True, null=True, verbose_name="晚归理由")
    material = models.FileField(upload_to="attendance_materials/", blank=True, null=True, verbose_name="证明材料")
    msg = models.CharField(max_length=200, verbose_name="打卡备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "打卡记录"
        verbose_name_plural = "打卡记录"
        unique_together = [["student", "check_config"]]  # 每轮查寝一个学生仅一条记录

    def __str__(self):
        return f"{self.student_name} - {self.check_config.config_name} - {self.check_status}"