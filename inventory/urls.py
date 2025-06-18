from rest_framework.routers import DefaultRouter
from .views import MedicalDeviceViewSet, MedicineViewSet


router = DefaultRouter()
router.register(r'medicines', MedicineViewSet, basename='medicine')
router.register(r'devices', MedicalDeviceViewSet, basename='device')

urlpatterns = router.urls
