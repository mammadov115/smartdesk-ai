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
    list_display = ("id", "display_owner", "display_message_count", "created_at")
    search_fields = ("owner__email",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("owner", "created_at", "updated_at")
    inlines = [ChatMessageInline]

    fieldsets = (
        ("Session", {"fields": ("owner", "created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Owner")
    def display_owner(self, obj):
        return obj.owner.email

    @display(description="Messages")
    def display_message_count(self, obj):
        return obj.messages.count()
