from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from orders.urls import order_router, cart_router  

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core API endpoints
    path('medical_stores/', include('medical_stores.urls')), 
    path('inventory/', include('inventory.urls')),
    path('payment/', include('payments.urls')),

    # Orders and Cart 
    path('orders/', include(order_router.urls)),
    path('cart/', include('cart.urls')),
    path("AI-chat/", include("AI_chat.urls")),

    # Additional APIs
    path('reviews/', include('reviews.urls')),
    path('notification/', include('notifications.urls')),

    # User-related endpoints (login/register/profile/etc.)
    path('users/', include('users.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
