from .models import Notification
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

User = get_user_model()

def send_real_time_notification(notification):
    try:
        channel_layer = get_channel_layer()
        group_name = f"user_{notification.sent_to.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send.notification",
                "message": {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                    "priority": notification.priority,
                    # "notification_type": notification.notification_type
                }
            }
        )
    except Exception as e:
        print(f"Error sending real-time notification: {str(e)}")

def notify_user(user_id, title, message, priority='medium', notification_type='system', data=None):
    try:
        user = User.objects.get(id=user_id)
        notification = create_notification(
            sent_to=user,
            title=title,
            message=message,
            priority=priority,
            notification_type=notification_type,
            data=data
        )
        send_real_time_notification(notification)
        return notification
    except User.DoesNotExist:
        return None