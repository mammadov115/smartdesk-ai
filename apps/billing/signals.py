import logging

from django.dispatch import receiver

import djstripe.models
from djstripe.signals import WEBHOOK_SIGNALS

from apps.accounts.models import CompanyProfile

logger = logging.getLogger(__name__)


def _user_from_customer(customer_id):
    try:
        return djstripe.models.Customer.objects.get(id=customer_id).subscriber
    except djstripe.models.Customer.DoesNotExist:
        logger.warning("No dj-stripe Customer found for id=%s", customer_id)
        return None


@receiver(WEBHOOK_SIGNALS["checkout.session.completed"])
def on_checkout_completed(sender, event, **kwargs):
    """Stripe checkout succeeded → activate the paid plan."""
    session = event.data["object"]
    user = _user_from_customer(session.get("customer"))
    if user:
        CompanyProfile.objects.filter(owner=user).update(
            subscription_plan=CompanyProfile.SubscriptionPlan.PAID
        )
        logger.info("Plan upgraded to PAID for user %s", user.email)


@receiver(WEBHOOK_SIGNALS["invoice.payment_succeeded"])
def on_payment_succeeded(sender, event, **kwargs):
    """Recurring invoice paid → ensure plan stays active."""
    invoice = event.data["object"]
    # Only act on subscription invoices (not one-off)
    if not invoice.get("subscription"):
        return
    user = _user_from_customer(invoice.get("customer"))
    if user:
        CompanyProfile.objects.filter(owner=user).update(
            subscription_plan=CompanyProfile.SubscriptionPlan.PAID
        )


@receiver(WEBHOOK_SIGNALS["invoice.payment_failed"])
def on_payment_failed(sender, event, **kwargs):
    """Payment failed → log and optionally notify the user."""
    invoice = event.data["object"]
    user = _user_from_customer(invoice.get("customer"))
    if user:
        logger.warning(
            "Invoice payment failed for user %s (attempt %s)",
            user.email,
            invoice.get("attempt_count"),
        )
        # TODO: send failure notification email via services._send_mail


@receiver(WEBHOOK_SIGNALS["customer.subscription.deleted"])
def on_subscription_deleted(sender, event, **kwargs):
    """Subscription cancelled/expired → downgrade back to free."""
    subscription = event.data["object"]
    user = _user_from_customer(subscription.get("customer"))
    if user:
        CompanyProfile.objects.filter(owner=user).update(
            subscription_plan=CompanyProfile.SubscriptionPlan.FREE
        )
        logger.info("Plan downgraded to FREE for user %s", user.email)
