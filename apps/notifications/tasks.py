import logging

from celery import shared_task
from django.utils import timezone

from apps.accounts.models import CompanyProfile
from apps.chat.models import ChatSession

from .models import NotificationLog, NotificationPreference
from .services import (
    send_operator_handoff_email,
    send_unanswered_email,
    send_weekly_summary_email,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_operator_handoff(self, session_id: int) -> None:
    """
    Triggered immediately when a session is escalated to a human operator.
    Sends an email to the company if they have opted in.
    """
    try:
        session = ChatSession.objects.select_related(
            "owner__company_profile"
        ).get(pk=session_id)
    except ChatSession.DoesNotExist:
        logger.warning(
            "notify_operator_handoff: session %s not found — skipping.",
            session_id,
        )
        return

    try:
        company = session.owner.company_profile
    except CompanyProfile.DoesNotExist:
        logger.warning(
            "notify_operator_handoff: no company profile for owner %s — skipping.",
            session.owner.pk,
        )
        return

    try:
        send_operator_handoff_email(company, session)
    except Exception as exc:
        logger.exception(
            "notify_operator_handoff failed for session %s", session_id
        )
        raise self.retry(exc=exc)


@shared_task
def check_unanswered_conversations() -> None:
    """
    Periodic task (runs every 15 minutes via Celery beat).

    Finds WAITING sessions that have been silent beyond each company's configured
    threshold and sends a one-time unanswered-conversation email.
    Deduplication: once a session has been reported, a NotificationLog entry
    prevents further emails for the same session.
    """
    now = timezone.now()
    waiting_sessions = ChatSession.objects.filter(
        status=ChatSession.Status.WAITING
    ).select_related("owner__company_profile")

    for session in waiting_sessions:
        try:
            company = session.owner.company_profile
        except CompanyProfile.DoesNotExist:
            continue

        prefs, _ = NotificationPreference.objects.get_or_create(
            company=company
        )
        if not prefs.notify_on_unanswered:
            continue

        # Check silence threshold
        threshold = timezone.timedelta(
            minutes=prefs.unanswered_threshold_minutes
        )
        if now - session.updated_at < threshold:
            continue

        # Deduplication: only one email per session
        already_notified = NotificationLog.objects.filter(
            company=company,
            notification_type=NotificationLog.Type.UNANSWERED,
            session=session,
        ).exists()
        if already_notified:
            continue

        try:
            send_unanswered_email(company, session)
        except Exception:
            logger.exception(
                "check_unanswered_conversations: failed to send for session %s",
                session.pk,
            )


@shared_task
def send_weekly_analytics_summary() -> None:
    """
    Periodic task (runs every Monday at 08:00 local time via Celery beat).
    Sends a weekly analytics summary to every company that has opted in.
    """
    for company in CompanyProfile.objects.select_related("owner").all():
        try:
            send_weekly_summary_email(company)
        except Exception:
            logger.exception(
                "send_weekly_analytics_summary: failed for company %s",
                company.pk,
            )
