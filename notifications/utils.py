import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Notification
from users.models import User  # Import your User model

logger = logging.getLogger(__name__)

def send_notification(
    user,
    message,
    notification_type='system',
    data=None,
    send_email=False,
    email_subject=None,
    email_template=None,
    email_context=None
):
    """
    Creates a notification for a user and optionally sends an email
    Author:Ahmed M.Salah
    Args:
        user: User instance
        message: Notification message content
        notification_type: Type of notification (default: 'system')
        data: Extra JSON data for the notification
        send_email: Whether to send an email (default: False)
        email_subject: Email subject
        email_template: Path to email template
        email_context: Context for email template
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
    
    # Render template if provided, otherwise use notification message
    if template:
        try:
            message = render_to_string(template, context)
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            message = notification.message
    else:
        message = notification.message
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
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


