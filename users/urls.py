# users/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenObtainPairView, verify_email, PharmacistViewSet, ClientViewSet, ClientViewprofile  # Added ClientViewprofile import
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'pharmacists', PharmacistViewSet, basename='pharmacist')
router.register(r'clients', ClientViewSet, basename='client')
urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/<str:token>/', verify_email, name='verify-email'),
    path('client/profile/', ClientViewprofile.as_view(), name='client-profile'),
    # [AMS] --> postponed for future 
    # path('forget-password/', forget_password, name='forget-password'),
    # path('reset-password/<str:token>/', validate_reset_password, name='reset-password'),
] + router.urls
