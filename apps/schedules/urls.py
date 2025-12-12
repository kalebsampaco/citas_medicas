from rest_framework.routers import DefaultRouter

from .views import ScheduleViewSet

router = DefaultRouter()
router.register(r"", ScheduleViewSet, basename="schedule")

urlpatterns = router.urls
