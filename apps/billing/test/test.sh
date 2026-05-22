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

# ── 4. INVOICE HISTORY ────────────────────────────────────────────────────────
# Returns a list of invoices for the authenticated user, newest first.
# Each entry includes: id, created, amount_paid, currency, status,
# hosted_invoice_url, and invoice_pdf.
# An empty list is returned if the user has no Stripe Customer yet.
curl -s $BASE/api/billing/invoices/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 5. USAGE — free plan ──────────────────────────────────────────────────────
# Shows current monthly usage counters alongside each feature limit.
# On the free plan:
#   conversations.limit = 100, documents.limit = 3, operator_allowed = false
# Run this BEFORE upgrading to verify the free-plan baseline.
curl -s $BASE/api/billing/usage/ \
  -H "Authorization: Bearer $ACCESS" | jq

# Expected shape:
# {
#   "plan": "free",
#   "operator_allowed": false,
#   "conversations": { "used": <n>, "limit": 100 },
#   "documents":      { "used": <n>, "limit": 3 }
# }

# ── 6. USAGE — after upgrading to paid plan ───────────────────────────────────
# After checkout.session.completed is processed the plan switches to "paid".
# Re-run this to confirm:
#   conversations.limit = null, documents.limit = null, operator_allowed = true
curl -s $BASE/api/billing/usage/ \
  -H "Authorization: Bearer $ACCESS" | jq

# Expected shape:
# {
#   "plan": "paid",
#   "operator_allowed": true,
#   "conversations": { "used": <n>, "limit": null },
#   "documents":      { "used": <n>, "limit": null }
# }

# ── 7. OPERATOR GATING — free plan: escalation must be skipped ───────────────
# On the free plan, a fallback answer must NOT trigger operator escalation.
# Steps:
#   1. Ensure the user is on the FREE plan (check /api/billing/usage/).
#   2. Create a chat session.
#   3. Ask a question that has no matching knowledge chunk so the RAG pipeline
#      returns a fallback.
#   4. Check the server logs — you should see:
#        "Operator escalation skipped for session <id> — free plan."
#      and the session status must remain "ai" (not "waiting").

# 7a. Create a session
curl -s -X POST $BASE/api/chat/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" | jq

FREE_SESSION_ID=<paste session id here>

# 7b. Trigger a fallback (question with no knowledge)
curl -s -X POST $BASE/api/chat/sessions/$FREE_SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"What is the airspeed velocity of an unladen swallow?"}' | jq

# 7c. Verify session status is still "ai" (not escalated to "waiting")
curl -s $BASE/api/chat/sessions/$FREE_SESSION_ID/ \
  -H "Authorization: Bearer $ACCESS" | jq '.status'
# Expected output: "ai"

# ── 8. OPERATOR GATING — paid plan: escalation must fire ─────────────────────
# After upgrading, the same fallback flow should escalate the session.
# Steps:
#   1. Upgrade via checkout (section 1) and confirm /api/billing/usage/ shows paid.
#   2. Repeat steps 7a-7c with the paid account.

# 8a. Create a session (paid user)
curl -s -X POST $BASE/api/chat/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" | jq

PAID_SESSION_ID=<paste session id here>

# 8b. Trigger a fallback
curl -s -X POST $BASE/api/chat/sessions/$PAID_SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"What is the airspeed velocity of an unladen swallow?"}' | jq

# 8c. Verify session status has been escalated to "waiting"
curl -s $BASE/api/chat/sessions/$PAID_SESSION_ID/ \
  -H "Authorization: Bearer $ACCESS" | jq '.status'
# Expected output: "waiting"
