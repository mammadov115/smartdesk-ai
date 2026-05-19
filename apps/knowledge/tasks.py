import logging

from celery import shared_task

from .models import KnowledgeDocument
from .services import process_document

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_document_task(self, document_id: int) -> None:
    try:
        document = KnowledgeDocument.objects.get(pk=document_id)
    except KnowledgeDocument.DoesNotExist:
        logger.error("KnowledgeDocument %s not found — skipping.", document_id)
        return

    try:
        process_document(document)
        document.status = KnowledgeDocument.Status.READY
        document.error_message = ""
        document.save(update_fields=["status", "error_message", "updated_at"])
        logger.info("Document %s processed successfully.", document_id)
    except Exception as exc:
        logger.exception("Error processing document %s: %s", document_id, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            document.status = KnowledgeDocument.Status.FAILED
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message", "updated_at"])
