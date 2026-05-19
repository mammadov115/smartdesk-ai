BASE=http://localhost:8000

# ── PREREQUISITE: LOGIN  →  save tokens ───────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq

# store for subsequent requests:
ACCESS=<paste access token>

# ── 1. CREATE CHECKOUT SESSION ────────────────────────────────────────────────
# Returns a Stripe-hosted payment URL. Open checkout_url in a browser.
# price_id comes from your Stripe dashboard (Stripe test mode → Products → Price ID)
curl -s -X POST $BASE/api/billing/checkout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"price_id":"price_XXXXXXXXXXXXXXXX"}' | jq

# ── 2. CREATE CUSTOMER PORTAL SESSION ─────────────────────────────────────────
# Returns a Stripe-hosted portal URL where the user can manage / cancel their plan.
# Requires the user to already have a Stripe Customer (created on first checkout).
curl -s -X POST $BASE/api/billing/portal/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 3. WEBHOOK  (Stripe → your backend) ───────────────────────────────────────
# dj-stripe handles signature verification automatically.
# For local testing, forward events with the Stripe CLI:
#
#   stripe listen --forward-to localhost:8000/stripe/webhook/
#
# Copy the printed signing secret (whsec_...) into .envs/.local/.env:
#   DJSTRIPE_WEBHOOK_SECRET=whsec_...
#
# Then trigger events manually:
#   stripe trigger checkout.session.completed
#   stripe trigger invoice.payment_succeeded
#   stripe trigger invoice.payment_failed
#   stripe trigger customer.subscription.deleted
