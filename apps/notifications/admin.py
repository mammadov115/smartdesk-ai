from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter
from unfold.decorators import display

from .models import NotificationLog, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display = [
        "company",
        "display_operator_handoff",
        "display_unanswered",
        "unanswered_threshold_minutes",
        "display_weekly_summary",
        "notification_email",
        "updated_at",
    ]
    list_filter = [
        ("notify_on_operator_handoff", ChoicesDropdownFilter),
        ("notify_on_unanswered", ChoicesDropdownFilter),
        ("weekly_summary", ChoicesDropdownFilter),
    ]
    search_fields = ["company__name", "notification_email"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {"fields": ("company", "notification_email")},
        ),
        (
            "Operator Handoff",
            {"fields": ("notify_on_operator_handoff",)},
        ),
        (
            "Unanswered Conversations",
            {"fields": ("notify_on_unanswered", "unanswered_threshold_minutes")},
        ),
        (
            "Weekly Summary",
            {"fields": ("weekly_summary",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @display(boolean=True, description="Operator handoff")
    def display_operator_handoff(self, obj):
        return obj.notify_on_operator_handoff

    @display(boolean=True, description="Unanswered")
    def display_unanswered(self, obj):
        return obj.notify_on_unanswered

    @display(boolean=True, description="Weekly summary")
    def display_weekly_summary(self, obj):
        return obj.weekly_summary


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ["company", "display_type", "session", "recipient_email", "sent_at"]
    list_filter = [("notification_type", ChoicesDropdownFilter)]
    search_fields = ["company__name", "recipient_email"]
    readonly_fields = ["company", "notification_type", "session", "recipient_email", "sent_at"]
    date_hierarchy = "sent_at"
    ordering = ["-sent_at"]

    @display(description="Type", label=True)
    def display_type(self, obj):
        return obj.notification_type

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
