from rest_framework.permissions import BasePermission


def _has_role(request, *roles):
    return request.user.is_authenticated and request.user.role in roles


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request, 'STUDENT')


class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request, 'INSTRUCTOR')


class IsStaff(BasePermission):
    """Moniteur, superviseur ou admin."""
    def has_permission(self, request, view):
        return _has_role(request, 'INSTRUCTOR', 'SUPERVISOR', 'ADMIN')


class IsSupervisorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request, 'SUPERVISOR', 'ADMIN')
