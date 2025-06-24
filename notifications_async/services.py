from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def create_notification(
    sent_to,
    title,
    message,
    priority='medium',
    notification_type='system',
    data=None,
    created_by=None
):
    return Notification.objects.create(
        sent_to=sent_to,
        created_by=created_by,
        title=title,
        priority=priority,
        message=message,
        data=data or {},
        notification_type=notification_type
    )