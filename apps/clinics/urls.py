from rest_framework.routers import DefaultRouter

from .views import ClinicViewSet, RoomViewSet

router = DefaultRouter()
router.register(r"clinics", ClinicViewSet, basename="clinic")
router.register(r"rooms", RoomViewSet, basename="room")

urlpatterns = router.urls
