# users/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PharmacistViewSet, ClientViewSet

router = DefaultRouter()
#[OKS]  add  pharmacist and client viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'pharmacists', PharmacistViewSet, basename='pharmacist')
router.register(r'clients', ClientViewSet, basename='client')
urlpatterns = router.urls
