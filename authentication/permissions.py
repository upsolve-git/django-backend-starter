from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

# class used to determine the permission of each request.
class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        if not self.custom_check(request):
            raise PermissionDenied("You do not have permission to access this resource.")
        return True

    def custom_check(self, request):
        return True  