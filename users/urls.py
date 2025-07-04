# users/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenObtainPairView, verify_email, PharmacistViewSet, ClientViewSet, get_logged_in_user, get_logged_in_pharmacist, ClientViewprofile, get_current_user_profile,GoogleLoginView, DeliveryViewSet
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'pharmacists', PharmacistViewSet, basename='pharmacist')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/<str:token>/', verify_email, name='verify-email'),
    path('client/profile/', ClientViewprofile.as_view(), name='client-profile'),
    # path('me/', get_logged_in_user, name='get-logged-in-user'),

    # [SENU]: add endpoint to get the current user, pharma, client
    path('me/pharmacist/', get_logged_in_pharmacist, name='get-logged-in-pharmacist'),

    # [SENU] : get current user with image
    path('me/', get_current_user_profile, name='get-current-user'),
    
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),

    # [AMS] --> postponed for future 
    # path('forget-password/', forget_password, name='forget-password'),
    # path('reset-password/<str:token>/', validate_reset_password, name='reset-password'),
] + router.urls
