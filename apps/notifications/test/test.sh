BASE=http://localhost:8000

# ── PREREQUISITE: LOGIN  →  save access token ─────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq

# Store the access token for subsequent requests:
ACCESS=<paste access token here>

# ── 1. GET PREFERENCES  (auto-creates defaults on first access) ───────────────
# Returns the current company's notification settings.
# A default row is created automatically if none exists yet.
curl -s $BASE/api/notifications/preferences/me/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 2. DISABLE OPERATOR HANDOFF EMAIL ────────────────────────────────────────
# PATCH is partial — only the fields you send are changed.
curl -s -X PATCH $BASE/api/notifications/preferences/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"notify_on_operator_handoff": false}' | jq

# ── 3. SET UNANSWERED THRESHOLD TO 60 MINUTES ────────────────────────────────
# A WAITING session must be silent for this many minutes before the
# check_unanswered_conversations task fires an email.
curl -s -X PATCH $BASE/api/notifications/preferences/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"unanswered_threshold_minutes": 60}' | jq

# ── 4. OVERRIDE THE RECIPIENT EMAIL ──────────────────────────────────────────
# All three notification types will be sent to this address instead of the
# company owner's email when this field is non-empty.
curl -s -X PATCH $BASE/api/notifications/preferences/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"notification_email": "alerts@example.com"}' | jq

# ── 5. DISABLE WEEKLY SUMMARY ────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/notifications/preferences/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"weekly_summary": false}' | jq

# ── 6. VERIFY CURRENT STATE ───────────────────────────────────────────────────
curl -s $BASE/api/notifications/preferences/me/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 7. RESTORE DEFAULTS ───────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/notifications/preferences/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{
    "notify_on_operator_handoff": true,
    "notify_on_unanswered": true,
    "unanswered_threshold_minutes": 30,
    "weekly_summary": true,
    "notification_email": ""
  }' | jq

