from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class KnowledgeDocument(models.Model):
    class SourceType(models.TextChoices):
        PDF = "pdf", "PDF"
        DOCX = "docx", "Word"
        TXT = "txt", "Text File"
        TEXT = "text", "Plain Text"
        FAQ = "faq", "FAQ"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_documents",
    )
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    # File upload (PDF / DOCX / TXT)
    file = models.FileField(upload_to="knowledge/", blank=True, null=True)
    # Pasted text or FAQ Q+A (pre-formatted by the serializer)
    raw_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.source_type})"


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=1536)

    class Meta:
        ordering = ["chunk_index"]
        unique_together = [("document", "chunk_index")]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document_id}"
