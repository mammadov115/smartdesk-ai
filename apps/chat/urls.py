from rest_framework.routers import DefaultRouter

from .views import ChatSessionViewSet

router = DefaultRouter()
router.register("api/chat/sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = router.urls
