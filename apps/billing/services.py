import stripe
from django.conf import settings

import djstripe.models

stripe.api_key = settings.STRIPE_SECRET_KEY


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
