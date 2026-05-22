import logging

from rest_framework import mixins, permissions
from rest_framework.viewsets import GenericViewSet

from .models import KnowledgeDocument
from .serializers import KnowledgeDocumentSerializer
from .tasks import process_document_task

logger = logging.getLogger(__name__)


class KnowledgeDocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KnowledgeDocument.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        company = getattr(self.request.user, "company_profile", None)
        if company:
            from apps.billing.services import check_document_limit, increment_documents

            check_document_limit(company)
        document = serializer.save(
            owner=self.request.user,
            status=KnowledgeDocument.Status.PROCESSING,
        )
        if company:
            increment_documents(company)
        try:
            process_document_task.delay(document.pk)
        except Exception:
            logger.exception(
                "Failed to enqueue process_document_task for document %s. Is the Celery broker (Redis) reachable?",
                document.pk,
            )
            document.status = KnowledgeDocument.Status.FAILED
            document.error_message = "Could not enqueue processing task. Check broker connectivity."
            document.save(update_fields=["status", "error_message", "updated_at"])
