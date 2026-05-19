from rest_framework import mixins, permissions
from rest_framework.viewsets import GenericViewSet

from .models import KnowledgeDocument
from .serializers import KnowledgeDocumentSerializer
from .tasks import process_document_task


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
        document = serializer.save(
            owner=self.request.user,
            status=KnowledgeDocument.Status.PROCESSING,
        )
        process_document_task.delay(document.pk)
