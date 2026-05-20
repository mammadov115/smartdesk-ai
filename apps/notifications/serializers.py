from rest_framework import serializers

from .models import NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "notify_on_operator_handoff",
            "notify_on_unanswered",
            "unanswered_threshold_minutes",
            "weekly_summary",
            "notification_email",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
