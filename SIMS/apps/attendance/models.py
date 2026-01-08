from django.db import models
from django.conf import settings

class Attendance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lat = models.FloatField(verbose_name="纬度")
    lng = models.FloatField(verbose_name="经度")
    distance = models.FloatField(verbose_name="距离(米)")
    is_normal = models.BooleanField(default=True, verbose_name="是否正常")
    msg = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)