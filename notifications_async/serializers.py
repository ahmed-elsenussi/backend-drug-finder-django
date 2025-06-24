from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='notification_type', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'