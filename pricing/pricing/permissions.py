# pricing/permissions.py
from rest_framework.permissions import BasePermission

def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

class IsPricingManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and user_in_group(request.user, 'pricing_manager')

class IsRegionalManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and user_in_group(request.user, 'regional_manager')
