BASE=http://localhost:8000

# ── 1. REGISTER ────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"StrongPass1!"}' | jq

# ── 2. VERIFY EMAIL ────────────────────────────────────────────────────────────
# grab uid & token from the email printed to your terminal / Mailpit UI
curl -s -X POST $BASE/api/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"uid":"<uid>","token":"<token>"}' | jq

# ── 3. LOGIN  →  save tokens ───────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq
# response: { "access": "...", "refresh": "..." }

# store for subsequent requests:
ACCESS=<paste access token>
REFRESH=<paste refresh token>

# ── 4. LOGOUT  (blacklists the refresh token) ──────────────────────────────────
curl -s -X POST $BASE/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d "{\"refresh\":\"$REFRESH\"}" | jq

# ── 5. FORGOT PASSWORD ─────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/password/forgot/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com"}' | jq

# ── 6. RESET PASSWORD ──────────────────────────────────────────────────────────
# grab uid & token from the reset email
curl -s -X POST $BASE/api/auth/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{"uid":"<uid>","token":"<token>","password":"NewStrongPass1!"}' | jq

# ── 7. COMPANY PROFILE — GET ───────────────────────────────────────────────────
curl -s $BASE/api/company/me/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 8. COMPANY PROFILE — PATCH ────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/company/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"contact_email":"contact@acme.com","phone_number":"+1234567890","website":"https://acme.com"}' | jq


# ── PREREQUISITE: LOGIN  →  save access token ─────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq

# Store the access token for subsequent requests:
ACCESS=<paste access token here>


# ════════════════════════════════════════════════════════════════════════════════
# EMBED TOKEN
# ════════════════════════════════════════════════════════════════════════════════

# ── 1. GET COMPANY PROFILE — verify embed_token field is present ──────────────
# embed_token, chat_color, and chat_icon are now returned alongside existing fields.
# embed_token is read-only — it cannot be changed via PATCH.
curl -s $BASE/api/company/me/ \
  -H "Authorization: Bearer $ACCESS" | jq '{embed_token, chat_name, chat_color, chat_icon}'

# Store the embed token:
EMBED_TOKEN=<paste embed_token here>

# ── 2. REGENERATE EMBED TOKEN ────────────────────────────────────────────────
# Issues a fresh UUID, invalidating the previous one immediately.
# Any widget script still using the old token will get 404 from the config endpoint.
curl -s -X POST $BASE/api/company/embed-token/regenerate/ \
  -H "Authorization: Bearer $ACCESS" | jq
# Expected: {"embed_token": "<new-uuid>"}

# Update the stored variable with the new value:
EMBED_TOKEN=<paste new embed_token here>

# ── 3. VERIFY OLD TOKEN IS DEAD ───────────────────────────────────────────────
# Replace OLD_TOKEN with the UUID you had before step 2.
curl -s -o /dev/null -w "%{http_code}\n" \
  $BASE/api/chat/widget/<old-embed-token>/config/
# Expected: 404


# ════════════════════════════════════════════════════════════════════════════════
# ALLOWED DOMAINS
# ════════════════════════════════════════════════════════════════════════════════

# ── 4. LIST ALLOWED DOMAINS (initially empty) ────────────────────────────────
curl -s $BASE/api/company/domains/ \
  -H "Authorization: Bearer $ACCESS" | jq
# Expected: []

# ── 5. ADD FIRST DOMAIN ──────────────────────────────────────────────────────
# Hostname only — no scheme, no path, no trailing slash.
curl -s -X POST $BASE/api/company/domains/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"domain": "acme.com"}' | jq
# Expected 201: {"id": 1, "domain": "acme.com"}

# Store the domain id for the delete step:
DOMAIN_ID=<paste id here>

# ── 6. ADD SECOND DOMAIN ─────────────────────────────────────────────────────
curl -s -X POST $BASE/api/company/domains/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"domain": "app.acme.com"}' | jq
# Expected 201: {"id": 2, "domain": "app.acme.com"}

# ── 7. IDEMPOTENCY — adding the same domain twice returns 200, not 201 ───────
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST $BASE/api/company/domains/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"domain": "acme.com"}'
# Expected: 200

# ── 8. LIST ALLOWED DOMAINS (two entries after steps 5 & 6) ─────────────────
curl -s $BASE/api/company/domains/ \
  -H "Authorization: Bearer $ACCESS" | jq
# Expected: both acme.com (step 5) and app.acme.com (step 6) listed

# ── 9. DELETE A DOMAIN ───────────────────────────────────────────────────────
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE $BASE/api/company/domains/$DOMAIN_ID/ \
  -H "Authorization: Bearer $ACCESS"
# Expected: 204

# ── 10. DELETE DOMAIN BELONGING TO ANOTHER COMPANY — expect 404 ──────────────
# Ownership is enforced: you can only delete your own domains.
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE $BASE/api/company/domains/9999/ \
  -H "Authorization: Bearer $ACCESS"
# Expected: 404

# ── 11. LIST AFTER DELETE ────────────────────────────────────────────────────
curl -s $BASE/api/company/domains/ \
  -H "Authorization: Bearer $ACCESS" | jq
# Expected: only app.acme.com remains


# ════════════════════════════════════════════════════════════════════════════════
# WIDGET CONFIG (public endpoint — no Authorization header)
# ════════════════════════════════════════════════════════════════════════════════

# ── 12. FETCH CONFIG WITH VALID EMBED TOKEN ───────────────────────────────────
# The frontend script tag calls this to apply styles before the widget loads.
curl -s $BASE/api/chat/widget/$EMBED_TOKEN/config/ | jq
# Expected: {"chat_name": "AI Assistant", "chat_color": "#0070f3", "chat_icon": null}

# ── 13. FETCH CONFIG WITH INVALID TOKEN — expect 404 ─────────────────────────
curl -s -o /dev/null -w "%{http_code}\n" \
  $BASE/api/chat/widget/00000000-0000-0000-0000-000000000000/config/
# Expected: 404

# ── 14. UPDATE WIDGET APPEARANCE ─────────────────────────────────────────────
# chat_color and chat_icon are editable via the existing PATCH /api/company/me/ endpoint.
curl -s -X PATCH $BASE/api/company/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"chat_name": "Support Bot", "chat_color": "#e63946"}' | jq '{chat_name, chat_color}'

# Verify the public config endpoint reflects the new values immediately:
curl -s $BASE/api/chat/widget/$EMBED_TOKEN/config/ | jq
# Expected: {"chat_name": "Support Bot", "chat_color": "#e63946", "chat_icon": null}


# ════════════════════════════════════════════════════════════════════════════════
# WS ORIGIN VALIDATION
# Requires a running server and wscat (npm install -g wscat).
# SESSION_ID must exist — create one via the chat test.sh first.
# ════════════════════════════════════════════════════════════════════════════════

SESSION_ID=<paste session id here>

# ── 15. ADD localhost TO ALLOWED DOMAINS ────────────────────────────────────
curl -s -X POST $BASE/api/company/domains/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"domain": "localhost"}' | jq

# ── 16. WS CONNECTION — ALLOWED ORIGIN ───────────────────────────────────────
# embed_token in query string; Origin header matches an entry in AllowedDomain.
# Run in a separate terminal:
wscat -c "ws://localhost:8000/ws/chat/$SESSION_ID/?embed_token=$EMBED_TOKEN" \
  -H "Origin: http://localhost:8000"
# Expected: connected

# ── 17. WS CONNECTION — BLOCKED ORIGIN ───────────────────────────────────────
# evil.com is not in the allowed list → middleware rejects before the consumer runs.
# Run in a separate terminal:
wscat -c "ws://localhost:8000/ws/chat/$SESSION_ID/?embed_token=$EMBED_TOKEN" \
  -H "Origin: http://evil.com"
# Expected: error: Unexpected server response: 403
