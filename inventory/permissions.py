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
