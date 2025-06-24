from django.db import models
from users.models import User  # [SENU]: assuming you have a User model here

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        MESSAGE = 'message', 'Message'
        ALERT = 'alert', 'Alert'
        REMINDER = 'reminder', 'Reminder'
        SYSTEM = 'system', 'System'

    # link to the user who receives the notification
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    # notification type
    type =models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    message = models.TextField()
    data = models.JSONField(blank=True, null=True ) # extra data

    # tracking
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

