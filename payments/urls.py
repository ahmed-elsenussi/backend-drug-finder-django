from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = router.urls + [
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
]
