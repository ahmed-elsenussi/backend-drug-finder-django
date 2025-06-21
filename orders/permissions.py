from rest_framework import permissions

# [SARA]: Custom permission for order access and update
class OrderAccessPermission(permissions.BasePermission):
    """
    - Clients can view their own orders only.
    - Pharmacists can view orders for their own stores and update status for their stores' orders only.
    - Admins can view and update all orders.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        # Admin can do anything
        if user.is_staff or user.is_superuser:
            return True
        # Client can only view their own orders
        if user.role == 'client':
            return obj.client.user == user and request.method in permissions.SAFE_METHODS
        # Pharmacist can view orders for their stores, and update status for their stores' orders
        if user.role == 'pharmacist':
            if obj.store and obj.store.owner.user == user:
                if request.method in permissions.SAFE_METHODS:
                    return True
                # Only allow PATCH/PUT for status field
                if request.method in ['PUT', 'PATCH']:
                    # Only allow updating status, not other fields
                    allowed_fields = {'order_status'}
                    if set(request.data.keys()).issubset(allowed_fields):
                        return True
            return False
        return False
