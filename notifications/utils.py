import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Notification
from .serializers import NotificationSerializer
from users.models import User
import json
import redis
from django.conf import settings

redis_conn = redis.Redis.from_url(settings.REDIS_URL)
logger = logging.getLogger(__name__)

def send_notification(
    user,
    message,
    notification_type='system',
    data=None,
    send_email=False,
    email_subject=None,
    email_template=None,
    email_context=None,
    realtime=True
):
    """
    Creates a notification for a user and optionally sends an email
    Args:
        user: User instance
        message: Notification message content
        notification_type: Type of notification (default: 'system')
        data: Extra JSON data for the notification
        send_email: Whether to send an email (default: False)
        email_subject: Email subject
        email_template: Path to email template
        email_context: Context for email template
        realtime: Whether to send realtime notification (default: True)
    """
    # Create the notification
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        message=message,
        data=data or {}
    )
    
    # Send email if requested
    if send_email:
        send_notification_email(
            user=user,
            notification=notification,
            subject=email_subject,
            template=email_template,
            context=email_context
        )
    
    if realtime:
        try:
            serializer = NotificationSerializer(notification)
            
            # Publish to Redis channel
            redis_conn.publish(
                "notifications", 
                json.dumps({
                    **serializer.data, # type: ignore
                    "user": user.id  # Add user ID for room targeting
                })
            )
        except Exception as e:
            logger.error(f"Redis publish error: {e}")
    
    return notification

def send_notification_email(
    user,
    notification,
    subject=None,
    template=None,
    context=None
):
    """
    Sends an email for a notification
    
    Args:
        user: User instance
        notification: Notification instance
        subject: Email subject
        template: Path to email template
        context: Context for email template
    """
    if not user.email:
        logger.warning(f"User {user.id} has no email address, skipping email send")
        return False
    
    # Prepare email content
    subject = subject or f"New Notification: {notification.type}"
    context = context or {}
    context.update({
        'user': user,
        'notification': notification,
        'message': notification.message,
    })
    
    # Render template if provided
    if template:
        try:
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            html_message = notification.message
            plain_message = notification.message
    else:
        html_message = notification.message
        plain_message = notification.message
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )
        return True
    except Exception as e:
        logger.error(f"Error sending notification email to {user.email}: {e}")
        return False

def mark_user_notifications_as_read(user):
    """Mark all unread notifications for a user as read"""
    updated = Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)
    return updated