from rest_framework import permissions

# [SARA]: Custom permission for pharmacist and admin access to medicines/devices
class IsPharmacistOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow pharmacists to manage their own store's medicines/devices.
    Admins can access all.
    """
    def has_permission(self, request, view):
        # Allow safe methods for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Only pharmacists and admins can create/update/delete
        return request.user and request.user.is_authenticated and (
            request.user.role == 'pharmacist' or request.user.is_staff or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Pharmacist can only access objects of their own store
        if hasattr(obj, 'store') and obj.store:
            pharmacist = getattr(obj.store, 'owner', None)
            return pharmacist and hasattr(pharmacist, 'user') and pharmacist.user == request.user
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow full CRUD for admin, read-only for others.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', None) == 'admin':
                return True
        return request.method in permissions.SAFE_METHODS

class IsAdminCRU(permissions.BasePermission):
    """
    Allow Create, Read, Update for admin, forbid DELETE.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser or getattr(user, 'role', None) == 'admin':
            if request.method == 'DELETE':
                return False
            return True
        return False
