# import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from notifications.consumers import NotificationConsumer
# from django.urls import path

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# django_asgi_app = get_asgi_application()

# websocket_urlpatterns = [
#     path('ws/notifications/<int:user_id>/', NotificationConsumer.as_asgi()),
# ]

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": URLRouter(websocket_urlpatterns),
# })