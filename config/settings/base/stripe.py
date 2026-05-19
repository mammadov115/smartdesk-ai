from .general import env

# STRIPE / dj-stripe
# ------------------------------------------------------------------------------
# https://dj-stripe.dev/configuration/
STRIPE_LIVE_MODE = env.bool("STRIPE_LIVE_MODE", default=False)
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")

DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_WEBHOOK_SECRET", default="")
DJSTRIPE_USE_NATIVE_JSONFIELD = True
# New installation: use "id". Existing installations use "djstripe_id".
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
# Link Stripe Customer → our User model (default, but explicit is better)
DJSTRIPE_SUBSCRIBER_MODEL = "accounts.User"

# Frontend URLs Stripe redirects to after checkout / portal exit
STRIPE_SUCCESS_URL = env(
    "STRIPE_SUCCESS_URL",
    default="http://localhost:3000/billing/success",
)
STRIPE_CANCEL_URL = env(
    "STRIPE_CANCEL_URL",
    default="http://localhost:3000/billing/cancel",
)
