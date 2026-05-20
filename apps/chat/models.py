from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    """One conversation thread owned by a user."""

    class Status(models.TextChoices):
        AI = "ai", "AI"
        WAITING = "waiting", "Waiting for Operator"
        LIVE = "live", "Live with Operator"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operated_sessions",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.AI,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.pk} — {self.owner} [{self.status}]"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        OPERATOR = "operator", "Operator"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    # Populated for assistant messages: which document chunks backed the answer.
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] session={self.session_id}"
