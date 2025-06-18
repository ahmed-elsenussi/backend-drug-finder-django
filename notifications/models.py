from django.db import models
from users.models import User

class Notification(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    sent_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_notifications')
    title = models.CharField(max_length=255, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=[('low', 'Low'),('medium', 'Medium'),('high', 'High')])
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

