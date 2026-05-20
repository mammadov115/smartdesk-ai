from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import NotificationPreferenceViewSet

app_name = "notifications"

router = SimpleRouter()
router.register(
    "api/notifications/preferences",
    NotificationPreferenceViewSet,
    basename="notification-preference",
)

urlpatterns = [
    path("", include(router.urls)),
]
