from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatSessionViewSet, WidgetConfigView

router = DefaultRouter()
router.register("api/chat/sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = router.urls + [
    path("api/chat/widget/<uuid:embed_token>/config/", WidgetConfigView.as_view(), name="widget-config"),
]
