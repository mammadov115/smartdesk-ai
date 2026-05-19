from rest_framework.routers import DefaultRouter

from .views import KnowledgeDocumentViewSet

router = DefaultRouter()
router.register("api/knowledge/documents", KnowledgeDocumentViewSet, basename="knowledge-document")

urlpatterns = router.urls
