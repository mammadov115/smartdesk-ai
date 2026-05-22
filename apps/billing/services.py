import djstripe.models
import stripe
from django.conf import settings
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import CompanyProfile

stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------------------------------------------------------------------------
# Plan limits
# ---------------------------------------------------------------------------

PLAN_LIMITS = {
    CompanyProfile.SubscriptionPlan.FREE: {"conversations": 100, "documents": 3, "operator": False},
    CompanyProfile.SubscriptionPlan.PAID: {"conversations": None, "documents": None, "operator": True},
}


def _limits_for(company: CompanyProfile) -> dict:
    return PLAN_LIMITS[company.subscription_plan]


def is_operator_allowed(company: CompanyProfile | None) -> bool:
    """Return True only if the company's plan includes the operator handoff feature."""
    if company is None:
        return False
    return bool(_limits_for(company)["operator"])


# ---------------------------------------------------------------------------
# Monthly usage helpers
# ---------------------------------------------------------------------------

def get_or_create_current_usage(company: CompanyProfile):
    from .models import MonthlyUsage

    now = timezone.now()
    usage, _ = MonthlyUsage.objects.get_or_create(
        company=company,
        year=now.year,
        month=now.month,
    )
    return usage


def check_conversation_limit(company: CompanyProfile) -> None:
    limits = _limits_for(company)
    if limits["conversations"] is None:
        return  # unlimited on paid plan
    usage = get_or_create_current_usage(company)
    if usage.conversations_count >= limits["conversations"]:
        raise ValidationError(
            {
                "detail": (
                    f"You have reached your monthly conversation limit of "
                    f"{limits['conversations']} on the free plan. "
                    "Please upgrade to continue."
                ),
                "code": "plan_limit_reached",
            }
        )


def check_document_limit(company: CompanyProfile) -> None:
    limits = _limits_for(company)
    if limits["documents"] is None:
        return  # unlimited on paid plan
    usage = get_or_create_current_usage(company)
    if usage.documents_count >= limits["documents"]:
        raise ValidationError(
            {
                "detail": (
                    f"You have reached your monthly document limit of "
                    f"{limits['documents']} on the free plan. "
                    "Please upgrade to continue."
                ),
                "code": "plan_limit_reached",
            }
        )


def increment_conversations(company: CompanyProfile) -> None:
    from .models import MonthlyUsage

    now = timezone.now()
    MonthlyUsage.objects.filter(
        company=company, year=now.year, month=now.month,
    ).update(conversations_count=F("conversations_count") + 1)


def increment_documents(company: CompanyProfile) -> None:
    from .models import MonthlyUsage

    now = timezone.now()
    MonthlyUsage.objects.filter(
        company=company, year=now.year, month=now.month,
    ).update(documents_count=F("documents_count") + 1)


def get_current_usage(user) -> dict:
    """
    Return a dict with the user's current plan, monthly usage counters,
    and per-feature limits.  Suitable for direct API serialisation.
    """
    company = getattr(user, "company_profile", None)
    if company is None:
        return {}
    limits = _limits_for(company)
    usage = get_or_create_current_usage(company)
    return {
        "plan": company.subscription_plan,
        "operator_allowed": limits["operator"],
        "conversations": {
            "used": usage.conversations_count,
            "limit": limits["conversations"],
        },
        "documents": {
            "used": usage.documents_count,
            "limit": limits["documents"],
        },
    }


# ---------------------------------------------------------------------------
# Stripe session helpers
# ---------------------------------------------------------------------------

def _get_or_create_customer(user) -> djstripe.models.Customer:
    customer, _ = djstripe.models.Customer.get_or_create(subscriber=user)
    return customer


def create_checkout_session(user, price_id: str) -> str:
    """Create a Stripe Checkout Session and return the hosted URL."""
    customer = _get_or_create_customer(user)
    session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=settings.STRIPE_CANCEL_URL,
    )
    return session.url


def create_portal_session(user) -> str:
    """Create a Stripe Customer Portal Session and return the hosted URL."""
    customer = _get_or_create_customer(user)
    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=settings.STRIPE_CANCEL_URL,
    )
    return session.url


# ---------------------------------------------------------------------------
# Invoice history
# ---------------------------------------------------------------------------

def get_invoices(user) -> list:
    """Return serializable invoice dicts for the user's Stripe invoices, newest first."""
    try:
        customer = djstripe.models.Customer.objects.get(subscriber=user)
    except djstripe.models.Customer.DoesNotExist:
        return []
    result = []
    for inv in djstripe.models.Invoice.objects.filter(customer=customer).order_by("-created"):
        sd = inv.stripe_data or {}
        # Stripe stores amounts in the currency's smallest unit (cents for USD).
        amount_paid_cents = sd.get("amount_paid", 0)
        result.append(
            {
                "id": inv.id,
                "created": inv.created,
                "amount_paid": round(amount_paid_cents / 100, 2),
                "currency": (sd.get("currency") or "").upper(),
                "status": sd.get("status", ""),
                "hosted_invoice_url": sd.get("hosted_invoice_url"),
                "invoice_pdf": sd.get("invoice_pdf"),
            }
        )
    return result
