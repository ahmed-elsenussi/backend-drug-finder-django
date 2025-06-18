from rest_framework.routers import DefaultRouter
from .views import MedicalStoreViewSet

router = DefaultRouter()
router.register(r'', MedicalStoreViewSet, basename='medical_store')

urlpatterns = router.urls
