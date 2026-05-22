import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.models import CompanyProfile

logger = logging.getLogger(__name__)

_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

_FREE_LIMITS = {"conversations": 100, "documents": 3}
_WARNING_THRESHOLD = 0.8


@shared_task
def reset_monthly_usage() -> None:
    """
    Periodic task — runs on the 1st of each month at 00:05.
    Pre-creates a MonthlyUsage row for every company so that the first limit
    check of the month never needs to INSERT under request load.
    """
    from .models import MonthlyUsage

    now = timezone.now()
    for company in CompanyProfile.objects.all():
        MonthlyUsage.objects.get_or_create(
            company=company,
            year=now.year,
            month=now.month,
        )
    logger.info("reset_monthly_usage: pre-created rows for %d/%02d", now.year, now.month)


@shared_task
def check_limit_warnings() -> None:
    """
    Periodic task — runs daily at 09:00.
    Sends a one-per-month warning email to any free-plan company that has
    consumed >= 80 % of their monthly conversation or document limit.
    """
    from .models import MonthlyUsage

    now = timezone.now()
    free_companies = (
        CompanyProfile.objects
        .filter(subscription_plan=CompanyProfile.SubscriptionPlan.FREE)
        .select_related("owner")
    )
    for company in free_companies:
        usage, _ = MonthlyUsage.objects.get_or_create(
            company=company, year=now.year, month=now.month,
        )
        if usage.limit_warning_sent:
            continue

        warnings = []
        if usage.conversations_count >= _FREE_LIMITS["conversations"] * _WARNING_THRESHOLD:
            warnings.append(
                f"Conversations: {usage.conversations_count}/{_FREE_LIMITS['conversations']}"
            )
        if usage.documents_count >= _FREE_LIMITS["documents"] * _WARNING_THRESHOLD:
            warnings.append(
                f"Documents: {usage.documents_count}/{_FREE_LIMITS['documents']}"
            )
        if not warnings:
            continue

        subject = f"[{company.name}] You're approaching your plan limits"
        body = (
            f"Hi,\n\n"
            f"You are approaching your monthly limits on the free plan:\n\n"
            + "\n".join(f"  \u2022 {w}" for w in warnings)
            + "\n\nUpgrade to a paid plan for unlimited usage.\n\n\u2014 SmartDesk AI"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=_FROM_EMAIL,
                recipient_list=[company.owner.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Limit warning email failed for company %s", company.pk)

        MonthlyUsage.objects.filter(pk=usage.pk).update(limit_warning_sent=True)
        logger.info("Limit warning sent for company %s", company.name)
