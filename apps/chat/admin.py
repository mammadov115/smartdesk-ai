from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import ChatMessage, ChatSession


class ChatMessageInline(TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content_preview", "sources", "created_at")
    fields = ("role", "content_preview", "sources", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @display(description="Content")
    def content_preview(self, obj):
        if len(obj.content) > 200:
            return obj.content[:200] + "…"
        return obj.content


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    list_display = ("id", "display_owner", "display_status", "display_operator", "display_message_count", "created_at")
    list_filter = ("status",)
    search_fields = ("owner__email", "operator__email")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("owner", "status", "operator", "created_at", "updated_at")
    inlines = [ChatMessageInline]

    fieldsets = (
        ("Session", {"fields": ("owner", "status", "operator", "created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Owner")
    def display_owner(self, obj):
        return obj.owner.email

    @display(description="Status")
    def display_status(self, obj):
        return obj.get_status_display()

    @display(description="Operator")
    def display_operator(self, obj):
        return obj.operator.email if obj.operator else "-"

    @display(description="Messages")
    def display_message_count(self, obj):
        return obj.messages.count()
