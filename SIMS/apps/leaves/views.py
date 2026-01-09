from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import LeaveRequest
from .serializers import LeaveSerializer
from .permissions import IsTeacher, IsOwnerAndEditable


class LeaveViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'student']

    def get_permissions(self):
        if self.action in ['approve', 'monitoring']:
            return [IsTeacher()]

        if self.action in ['cancel', 'report_back']:
            return [permissions.IsAuthenticated()]

        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsTeacher | IsOwnerAndEditable)()]

        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('student').all().order_by('-created_at')

        if getattr(user, 'role', None) != 'teacher':
            queryset = queryset.filter(student=user)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    def perform_create(self, serializer):
        serializer.save(student=self.request.user, status='pending')

    # --- 老师审批接口 ---
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """
        老师审批逻辑：修改状态并添加审批意见
        请求体示例：{"status": "approved", "comment": "同意，注意安全"}
        """
        leave_request = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')

        if new_status not in ['approved', 'rejected', 'returned']:
            return Response({"detail": "状态无效"}, status=400)

        leave_request.status = new_status
        leave_request.comment = comment
        leave_request.save()
        return Response({"message": "审批已完成"})

    # --- 学生撤销接口 ---
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        leave_request = self.get_object()
        # 补充：必须是本人才能撤销
        if leave_request.student != request.user:
            return Response({"detail": "无权操作"}, status=403)
        if leave_request.status != 'pending':
            return Response({"detail": "当前状态无法撤销"}, status=400)

        leave_request.status = 'canceled'
        leave_request.save()
        return Response({"message": "已撤销"})

    # --- 学生销假接口 ---
    @action(detail=True, methods=['post'])
    def report_back(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.student != request.user:
            return Response({"detail": "非本人操作"}, status=403)
        # 幂等性检查：如果已经销假，直接返回
        if leave_request.status == 'reported':
            return Response({"detail": "已销假，请勿重复操作"})
        if leave_request.status != 'approved':
            return Response({"detail": "未获准的假条无法销假"}, status=400)

        leave_request.status = 'reported'
        leave_request.report_back_time = timezone.now()
        leave_request.save()
        return Response({"message": "销假成功"})

    # --- 老师监控接口 ---
    @action(detail=False, methods=['get'], permission_classes=[IsTeacher])
    def monitoring(self, request):
        """
        URL: GET /api/leaves/monitoring/
        老师查看：1.已通过但未销假的人；2.超过预定时间未销假的人
        """
        now = timezone.now()
        # 1. 所有已通过但未销假的
        unreported = LeaveRequest.objects.filter(status='approved')

        # 2. 超过 end_time 还没销假的 (逾期)
        overdue = unreported.filter(end_time__lt=now)

        return Response({
            "unreported_count": unreported.count(),
            "overdue_count": overdue.count(),
            "overdue_list": LeaveSerializer(overdue, many=True).data,
            "all_active_list": LeaveSerializer(unreported, many=True).data
        })