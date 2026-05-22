from django.db import models

from apps.accounts.models import CompanyProfile
from apps.chat.models import ChatSession


class NotificationPreference(models.Model):
    """Per-company settings for which notifications to receive and how."""

    company = models.OneToOneField(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )

    # --- Operator handoff ---
    notify_on_operator_handoff = models.BooleanField(
        default=True,
        help_text="Send an email immediately when a session is escalated to a human operator.",
    )

    # --- Unanswered conversations ---
    notify_on_unanswered = models.BooleanField(
        default=True,
        help_text="Send an email when a waiting conversation has no operator response for too long.",
    )
    unanswered_threshold_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Minutes of silence in a WAITING session before the unanswered email fires.",
    )

    # --- Weekly summary ---
    weekly_summary = models.BooleanField(
        default=True,
        help_text="Receive a weekly analytics summary every Monday morning.",
    )

    # --- Recipient override ---
    notification_email = models.EmailField(
        blank=True,
        help_text=(
            "Override the email address that receives notifications. Defaults to the company owner's email when blank."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification prefs for {self.company.name}"

    def get_recipient_email(self) -> str:
        """Return the notification recipient, falling back to the owner's email."""
        return self.notification_email or self.company.owner.email


class NotificationLog(models.Model):
    """
    Audit trail and deduplication guard for sent notifications.

    For unanswered-conversation emails, the (company, notification_type, session)
    combination is checked before sending to ensure a session is only reported once.
    """

    class Type(models.TextChoices):
        OPERATOR_HANDOFF = "operator_handoff", "Operator Handoff"
        UNANSWERED = "unanswered", "Unanswered Conversation"
        WEEKLY_SUMMARY = "weekly_summary", "Weekly Summary"

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    recipient_email = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        return f"{self.notification_type} → {self.recipient_email} ({self.sent_at:%Y-%m-%d})"
