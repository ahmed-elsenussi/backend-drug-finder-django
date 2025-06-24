
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.mail import send_mail
from .utils import send_real_time_notification
from .models import Notification
from .serializers import NotificationSerializer
from django.shortcuts import get_object_or_404

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        # Only show notifications for logged-in user
        return Notification.objects.filter(sent_to=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Associate notification with current user
        notification = serializer.save(sent_to=self.request.user)
        
        try:
            send_real_time_notification(notification)
        except Exception as e:
            # Handle channel layer errors gracefully
            print(f"WebSocket error: {str(e)}")
        
        # Only send email for high priority notifications
        if notification.priority == 'high':
            self.send_email_notification(notification)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            sent_to=request.user, 
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
    
    def send_email_notification(self, notification):
        subject = f"URGENT: {notification.title}"
        message = f"""
        {notification.message}
        
        Priority: {notification.get_priority_display()}
        Sent at: {notification.created_at}
        """
        
        send_mail(
            subject,
            message,
            'notifications@drugfinder.com',
            [notification.sent_to.email],
            fail_silently=True,
        )