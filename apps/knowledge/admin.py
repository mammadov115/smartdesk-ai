from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter
from unfold.decorators import display

from .models import KnowledgeChunk, KnowledgeDocument
from .tasks import process_document_task


class KnowledgeChunkInline(TabularInline):
    model = KnowledgeChunk
    extra = 0
    readonly_fields = ("chunk_index", "content_preview")
    fields = ("chunk_index", "content_preview")
    can_delete = False
    show_change_link = False
    verbose_name = "Chunk"
    verbose_name_plural = "Chunks"

    def has_add_permission(self, request, obj=None):
        return False

    @display(description="Content")
    def content_preview(self, obj):
        return obj.content[:300] + "…" if len(obj.content) > 300 else obj.content


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(ModelAdmin):
    list_display = (
        "title",
        "owner",
        "display_source_type",
        "display_status",
        "display_chunk_count",
        "created_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("source_type", ChoicesDropdownFilter),
    )
    search_fields = ("title", "owner__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = (
        "owner",
        "source_type",
        "file",
        "raw_text",
        "status",
        "error_message",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {"fields": ("owner", "title", "source_type")},
        ),
        (
            "Content",
            {"fields": ("file", "raw_text")},
        ),
        (
            "Processing",
            {"fields": ("status", "error_message")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    inlines = [KnowledgeChunkInline]
    actions = ["reprocess_documents"]

    # ------------------------------------------------------------------ #
    # Display helpers                                                       #
    # ------------------------------------------------------------------ #

    @display(description="Source")
    def display_source_type(self, obj):
        return obj.get_source_type_display()

    @display(
        description="Status",
        label={
            KnowledgeDocument.Status.PROCESSING: "warning",
            KnowledgeDocument.Status.READY: "success",
            KnowledgeDocument.Status.FAILED: "danger",
        },
    )
    def display_status(self, obj):
        return obj.status

    @display(description="Chunks")
    def display_chunk_count(self, obj):
        return obj.chunks.count()

    # ------------------------------------------------------------------ #
    # Actions                                                               #
    # ------------------------------------------------------------------ #

    @admin.action(description="Reprocess selected documents")
    def reprocess_documents(self, request, queryset):
        count = 0
        for doc in queryset:
            doc.status = KnowledgeDocument.Status.PROCESSING
            doc.error_message = ""
            doc.save(update_fields=["status", "error_message", "updated_at"])
            try:
                process_document_task.delay(doc.pk)
                count += 1
            except Exception:
                doc.status = KnowledgeDocument.Status.FAILED
                doc.error_message = "Could not enqueue task. Is the broker running?"
                doc.save(update_fields=["status", "error_message", "updated_at"])

        self.message_user(request, f"{count} document(s) queued for reprocessing.")
