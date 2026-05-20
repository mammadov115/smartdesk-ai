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

# ── 8. TRIGGER OPERATOR HANDOFF NOTIFICATION (event smoke test) ──────────────
# The operator_handoff notification fires automatically when the AI cannot
# answer a question (fallback) and the session is still in AI status.
# Steps:
#   a) Create a new chat session.
#   b) Send a question the AI has no knowledge for → it returns a fallback.
#   c) The server queues notify_operator_handoff.delay(session_id) via Celery.
#   d) If session.status becomes "waiting", the handoff was triggered.

# a) Create a session — note the returned "id"
curl -s -X POST $BASE/api/chat/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{}' | jq

# Store session id:
SESSION=<paste session id here>

# b) Ask a question with no matching knowledge document (triggers fallback)
curl -s -X POST $BASE/api/chat/sessions/$SESSION/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question": "What is the airspeed velocity of an unladen swallow?"}' | jq

# c) Retrieve the session — if status is "waiting" the handoff fired and
#    notify_operator_handoff was queued on Celery. A NotificationLog row will
#    appear in the admin at /admin/notifications/notificationlog/
curl -s $BASE/api/chat/sessions/$SESSION/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 9. PERIODIC TASKS (unanswered + weekly summary) ──────────────────────────
# These tasks are not triggered by an HTTP request — they run on Celery Beat.
# To fire them synchronously during development (no worker needed), use the
# Django shell:
#
#   uv run --env-file .envs/.local/.env python manage.py shell \
#     --settings=config.settings.local
#
#   >>> from apps.notifications.tasks import check_unanswered_conversations
#   >>> check_unanswered_conversations()        # call directly — runs right now
#
#   >>> from apps.notifications.tasks import send_weekly_analytics_summary
#   >>> send_weekly_analytics_summary()         # call directly — runs right now
#
# NOTE: .delay() only queues the task to Redis; it runs only when a Celery
# worker is running. For local smoke-testing, always call the function
# directly so it executes in the current process immediately.
#
# Both tasks write a NotificationLog row per email sent.
# Confirm in the admin at /admin/notifications/notificationlog/

