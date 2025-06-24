from django.db import models
from users.models import User

class Notification(models.Model):
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    sent_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    title = models.CharField(max_length=255, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=[('low', 'Low'),('medium', 'Medium'),('high', 'High')])
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
        return self
    
    @classmethod
    def mark_all_read(cls, user):
        return cls.objects.filter(sent_to=user, is_read=False).update(is_read=True)
    
    @property
    def priority_class(self):
        return {
            'high': 'bg-red-50 text-red-700',
            'medium': 'bg-yellow-50 text-yellow-700',
            'low': 'bg-gray-50 text-gray-700'
        }.get(self.priority, '')
    
    @property
    def icon_details(self):
        icons = {
            'pharmacy': {
                'high': {'icon': 'AlertCircle', 'color': 'text-red-500'},
                'medium': {'icon': 'AlertCircle', 'color': 'text-yellow-500'},
                'low': {'icon': 'CheckCircle', 'color': 'text-green-500'}
            },
            'patient': {
                'high': {'icon': 'User', 'color': 'text-blue-500'},
                'medium': {'icon': 'User', 'color': 'text-blue-500'},
                'low': {'icon': 'User', 'color': 'text-blue-500'}
            },
            'system': {
                'high': {'icon': 'Bell', 'color': 'text-red-500'},
                'medium': {'icon': 'Bell', 'color': 'text-yellow-500'},
                'low': {'icon': 'Bell', 'color': 'text-gray-500'}
            }
        }
        return icons.get(self.notification_type, {}).get(self.priority, {'icon': 'Bell', 'color': 'text-gray-500'})