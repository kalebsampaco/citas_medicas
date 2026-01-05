from rest_framework import routers

from .views import ChatSessionViewSet

router = routers.DefaultRouter()
router.register(r"sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = router.urls
