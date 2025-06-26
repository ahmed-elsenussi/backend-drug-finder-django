from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelfPharmacistOrAdmin(BasePermission):
    """
    Allow pharmacists to edit their own profile and admins to edit any.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Allow read-only access for authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Admins can do anything
        if user.is_staff or user.role == 'admin':
            return True

        # Pharmacist can only update their own profile
        return hasattr(user, 'pharmacist') and obj.user == user
