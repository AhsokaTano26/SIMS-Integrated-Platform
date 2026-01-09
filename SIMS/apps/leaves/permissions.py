from rest_framework import permissions

class IsTeacher(permissions.BasePermission):
    """
    仅允许角色为 teacher 的用户通过验证
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'teacher'
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsOwnerOrTeacher(permissions.BasePermission):
    """
    对象级权限：允许老师查看所有，学生仅能查看/修改自己的数据
    """
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'role', None) == 'teacher':
            return True
        return obj.student == request.user


class IsOwnerAndEditable(permissions.BasePermission):
    """
    允许学生在 'pending' 或 'returned' 状态下修改自己的申请
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # 核心逻辑：本人且状态属于可编辑范畴
        return obj.student == request.user and obj.status in ['pending', 'returned']