from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from leaves.models import LeaveRequest
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = '快速生成测试用的老师、学生账号及请假数据'

    def handle(self, *args, **kwargs):
        self.stdout.write("正在清理旧数据...")
        # 慎用：这会删除除了超级用户以外的所有人
        User.objects.filter(is_superuser=False).delete()

        # 1. 创建老师账号
        self.stdout.write("创建老师账号...")
        teacher = User.objects.create_user(
            username='teacher1',
            password='password123',
            role='teacher',
            email='teacher@school.edu'
        )

        # 2. 创建一批学生账号
        self.stdout.write("创建学生账号...")
        students = []
        for i in range(1, 6):
            s = User.objects.create_user(
                username=f'student{i}',
                password='password123',
                role='student',
                email=f's{i}@student.com'
            )
            students.append(s)

        # 3. 为学生生成一些随机请假数据
        self.stdout.write("生成请假申请...")
        reasons = ["感冒发烧，需要去医院", "家里有急事处理", "参加校外实习面试", "回老家办身份证"]
        statuses = ['pending', 'approved', 'rejected']

        for s in students:
            for _ in range(random.randint(1, 3)):
                LeaveRequest.objects.create(
                    student=s,
                    start_time=timezone.now(),
                    end_time=timezone.now() + timezone.timedelta(days=2),
                    reason=random.choice(reasons),
                    status=random.choice(statuses)
                )

        self.stdout.write(self.style.SUCCESS('成功生成数据！'))
        self.stdout.write(f'老师账号: teacher1 / password123')
        self.stdout.write(f'学生账号: student1 到 student5 / password123')