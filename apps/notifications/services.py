import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.models import CompanyProfile
from apps.chat.models import ChatMessage, ChatSession

from .models import NotificationLog, NotificationPreference

logger = logging.getLogger(__name__)

_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_create_preferences(
    company: CompanyProfile,
) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(company=company)
    return prefs


def _send(subject: str, body: str, to: str) -> None:
    send_mail(
        subject=subject,
        message=body,
        from_email=_FROM_EMAIL,
        recipient_list=[to],
        fail_silently=False,
    )


# ---------------------------------------------------------------------------
# Notification senders
# ---------------------------------------------------------------------------


def send_operator_handoff_email(
    company: CompanyProfile, session: ChatSession
) -> None:
    """Send an immediate email when a session is escalated to a human operator."""
    prefs = _get_or_create_preferences(company)
    if not prefs.notify_on_operator_handoff:
        return

    recipient = prefs.get_recipient_email()
    subject = f"[{company.name}] Customer requesting a human operator"
    body = (
        f"Hi,\n\n"
        f"A customer has requested a human operator in conversation #{session.pk}.\n\n"
        f"Please log in to your dashboard to respond.\n\n"
        f"Session created: {session.created_at:%Y-%m-%d %H:%M} UTC\n\n"
        f"— SmartDesk AI"
    )

    try:
        _send(subject, body, recipient)
    except Exception:
        logger.exception(
            "Operator handoff email failed for session %s", session.pk
        )
    NotificationLog.objects.create(
        company=company,
        notification_type=NotificationLog.Type.OPERATOR_HANDOFF,
        session=session,
        recipient_email=recipient,
    )
    logger.info(
        "Operator handoff notification logged for session %s → %s",
        session.pk,
        recipient,
    )


def send_unanswered_email(
    company: CompanyProfile, session: ChatSession
) -> None:
    """Send an email when a WAITING conversation has had no operator response for too long."""
    prefs = _get_or_create_preferences(company)
    if not prefs.notify_on_unanswered:
        return

    recipient = prefs.get_recipient_email()

    last_msg = (
        ChatMessage.objects.filter(session=session, role=ChatMessage.Role.USER)
        .order_by("-created_at")
        .first()
    )
    question_preview = last_msg.content[:200] if last_msg else "(no message)"

    subject = f"[{company.name}] Unanswered conversation — {prefs.unanswered_threshold_minutes} min"
    body = (
        f"Hi,\n\n"
        f"Conversation #{session.pk} has had no operator response for over "
        f"{prefs.unanswered_threshold_minutes} minutes.\n\n"
        f'Last customer message:\n  "{question_preview}"\n\n'
        f"Please log in to your dashboard to respond.\n\n"
        f"— SmartDesk AI"
    )

    try:
        _send(subject, body, recipient)
    except Exception:
        logger.exception("Unanswered email failed for session %s", session.pk)
    NotificationLog.objects.create(
        company=company,
        notification_type=NotificationLog.Type.UNANSWERED,
        session=session,
        recipient_email=recipient,
    )
    logger.info(
        "Unanswered notification logged for session %s → %s",
        session.pk,
        recipient,
    )


def send_weekly_summary_email(company: CompanyProfile) -> None:
    """Send the weekly analytics summary to the company owner (or their override email)."""
    prefs = _get_or_create_preferences(company)
    if not prefs.weekly_summary:
        return

    stats = _gather_weekly_stats(company)
    recipient = prefs.get_recipient_email()

    most_asked_lines = (
        "\n".join(
            f'  {i + 1}. "{item["question"]}" ({item["count"]} times)'
            for i, item in enumerate(stats["most_asked"])
        )
        or "  (not enough data yet)"
    )

    subject = f"[{company.name}] Weekly Chat Summary"
    body = (
        f"Hi,\n\n"
        f"Here is your weekly chat summary for {company.name}:\n\n"
        f"Conversations started:   {stats['conversation_count']}\n"
        f"Messages exchanged:      {stats['message_count']}\n"
        f"Unanswered questions:    {stats['unanswered_count']}\n\n"
        f"Most Asked Topics\n"
        f"-----------------\n"
        f"{most_asked_lines}\n\n"
        f"Have a great week,\n"
        f"SmartDesk AI"
    )

    try:
        _send(subject, body, recipient)
    except Exception:
        logger.exception(
            "Weekly summary email failed for company %s", company.pk
        )
    NotificationLog.objects.create(
        company=company,
        notification_type=NotificationLog.Type.WEEKLY_SUMMARY,
        session=None,
        recipient_email=recipient,
    )
    logger.info(
        "Weekly summary notification logged for company %s → %s",
        company.name,
        recipient,
    )


# ---------------------------------------------------------------------------
# Stats helper for the weekly summary
# ---------------------------------------------------------------------------


def _gather_weekly_stats(company: CompanyProfile) -> dict:
    """Collect last-7-days stats for the weekly summary email."""
    from datetime import timedelta

    from apps.analytics.services import (
        get_most_asked_questions,
        get_unanswered_questions,
    )

    week_ago = timezone.now() - timedelta(days=7)
    sessions = ChatSession.objects.filter(
        owner=company.owner, created_at__gte=week_ago
    )
    conversation_count = sessions.count()
    message_count = ChatMessage.objects.filter(session__in=sessions).count()
    unanswered = get_unanswered_questions(company.owner)
    most_asked = get_most_asked_questions(company.owner, top_n=3)

    return {
        "conversation_count": conversation_count,
        "message_count": message_count,
        "unanswered_count": len(unanswered),
        "most_asked": most_asked,
    }
