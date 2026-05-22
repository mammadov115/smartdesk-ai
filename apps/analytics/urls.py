from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ConversationViewSet, QuestionViewSet, StatsViewSet

app_name = "analytics"

router = SimpleRouter()
router.register(
    "api/analytics/conversations",
    ConversationViewSet,
    basename="analytics-conversation",
)
router.register(
    "api/analytics/questions", QuestionViewSet, basename="analytics-question"
)
router.register(
    "api/analytics/stats", StatsViewSet, basename="analytics-stats"
)

urlpatterns = [
    path("", include(router.urls)),
]
