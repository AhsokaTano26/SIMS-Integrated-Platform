from django.db import models
from django.utils import timezone
from users.models import User, Dormitory  # 确保路径正确


class CheckConfig(models.Model):
    """查寝配置表（绝对时间点模式）"""
    config_name = models.CharField(max_length=100, verbose_name="查寝配置名称")

    # check_date 建议保留，用于后台按天筛选数据，但逻辑判定以 DateTimeField 为准
    check_date = models.DateField(verbose_name="查寝日期")

    # 【核心修改】全部使用 DateTimeField 存储完整的时间戳
    normal_start = models.DateTimeField(verbose_name="正常签到开始时间")
    normal_end = models.DateTimeField(verbose_name="正常签到结束时间")
    late_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="晚归截止时间（若无晚归则不填）"
    )

    # 其他配置
    valid_range = models.IntegerField(default=500, verbose_name="打卡有效范围（米）")
    need_material = models.BooleanField(default=False, verbose_name="是否需要上传证明材料")
    is_active = models.BooleanField(default=True, verbose_name="是否生效")

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_check_configs",
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "查寝配置"
        verbose_name_plural = "查寝配置"

    def save(self, *args, **kwargs):
        """
        不再需要重写 save 方法计算时长。
        逻辑校验已移至 View 层，确保存入的是经过校验的绝对时间。
        """
        # 自动同步 check_date 为开始时间的日期部分，方便管理后台筛选
        if self.normal_start:
            self.check_date = self.normal_start.date()
        super().save(*args, **kwargs)

    def __str__(self):
        # 格式化输出方便在后台查看
        start_str = timezone.localtime(self.normal_start).strftime("%Y-%m-%d %H:%M")
        return f"{self.config_name} ({start_str} 开始)"

    @property
    def current_status(self):
        """
        动态判定状态：
        1. 当前 < 开始 = 未开始
        2. 当前 > 截止 = 已结束
        3. 其余 = 进行中
        """
        now = timezone.now()  # 建议使用 timezone.now() 保持 UTC/时区一致

        # 确定最终截止时间点
        final_deadline = self.late_end if self.late_end else self.normal_end

        if now < self.normal_start:
            return "not_started"
        elif now > final_deadline:
            return "ended"
        else:
            return "in_progress"

    @property
    def status_display(self):
        """返回状态的中文描述，方便前端直接显示"""
        mapping = {
            "not_started": "未开始",
            "in_progress": "进行中",
            "ended": "已结束"
        }
        return mapping.get(self.current_status, "未知")

class Attendance(models.Model):
    """打卡记录表"""

    STATUS_NORMAL = "normal"
    STATUS_LATE = "late"

    STATUS_CHOICES = [
        (STATUS_NORMAL, "正常打卡"),
        (STATUS_LATE, "晚归打卡"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendances", verbose_name="学生")
    student_name = models.CharField(max_length=50, verbose_name="学生姓名")
    dorm = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name="attendances", verbose_name="寝室")
    check_config = models.ForeignKey(
        CheckConfig,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="查寝配置"
    )

    lat = models.FloatField(verbose_name="打卡纬度")
    lng = models.FloatField(verbose_name="打卡经度")
    distance = models.FloatField(verbose_name="与寝室距离（米）")

    check_time = models.DateTimeField(verbose_name="打卡时间")
    check_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_NORMAL,
        verbose_name="打卡状态"
    )

    late_reason = models.TextField(blank=True, null=True, verbose_name="晚归理由")
    material = models.FileField(
        upload_to="attendance_materials/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="证明材料"
    )
    msg = models.CharField(max_length=200, blank=True, null=True, verbose_name="打卡备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "打卡记录"
        verbose_name_plural = "打卡记录"
        # 确保同一场查寝一个学生只能打一次卡
        unique_together = [["student", "check_config"]]

    def __str__(self):
        return f"{self.student_name} - {self.check_config.config_name} - {self.get_check_status_display()}"

    def get_check_status_display(self) -> str:
        """显式声明以辅助 IDE 代码提示"""
        return dict(self.STATUS_CHOICES).get(self.check_status, self.check_status)