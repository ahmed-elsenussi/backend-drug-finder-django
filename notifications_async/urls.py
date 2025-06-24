from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('mark_all_read/', 
        NotificationViewSet.as_view({'post': 'mark_all_read'}), 
        name='mark-all-read'),
] + router.urls