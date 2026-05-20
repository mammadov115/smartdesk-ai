BASE=http://localhost:8000

# ── PREREQUISITE: LOGIN  →  save access token ─────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq

# Store the access token for subsequent requests:
ACCESS=<paste access token here>


# ════════════════════════════════════════════════════════════════════════════════
# CONVERSATIONS
# ════════════════════════════════════════════════════════════════════════════════

# ── 1. LIST CONVERSATIONS ─────────────────────────────────────────────────────
# Returns all chat sessions for the authenticated user with:
#   id, status, created_at, message_count, first_message_at,
#   last_message_at, duration_seconds
curl -s $BASE/api/analytics/conversations/ \
  -H "Authorization: Bearer $ACCESS" | jq

# Store a session id returned from the list above:
CONV_ID=<paste conversation id here>

# ── 2. RETRIEVE A CONVERSATION ────────────────────────────────────────────────
# Returns session metadata + full message history in chronological order.
# Each message includes: id, role, content, sources, created_at
curl -s $BASE/api/analytics/conversations/$CONV_ID/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 3. RETRIEVE A CONVERSATION — NOT FOUND ───────────────────────────────────
# Expect HTTP 404.
curl -s -o /dev/null -w "%{http_code}\n" \
  $BASE/api/analytics/conversations/99999/ \
  -H "Authorization: Bearer $ACCESS"


# ════════════════════════════════════════════════════════════════════════════════
# QUESTIONS
# ════════════════════════════════════════════════════════════════════════════════

# ── 4. MOST ASKED QUESTIONS ───────────────────────────────────────────────────
# Clusters user messages by cosine similarity (threshold 0.70).
# Returns up to 10 representative questions sorted by cluster size.
# If no user messages have embeddings stored yet, returns [].
curl -s "$BASE/api/analytics/questions/most-asked/" \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 5. UNANSWERED QUESTIONS ───────────────────────────────────────────────────
# Returns the last user message from each escalated session
# (status "waiting" or "live") — questions the AI could not resolve.
curl -s "$BASE/api/analytics/questions/unanswered/" \
  -H "Authorization: Bearer $ACCESS" | jq


# ════════════════════════════════════════════════════════════════════════════════
# STATS
# ════════════════════════════════════════════════════════════════════════════════

# ── 6. DAILY STATS (default) ──────────────────────────────────────────────────
# Returns conversation and message counts grouped by day, newest first.
# Fields: period (datetime), conversations, messages
curl -s "$BASE/api/analytics/stats/" \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 7. WEEKLY STATS ───────────────────────────────────────────────────────────
curl -s "$BASE/api/analytics/stats/?period=weekly" \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 8. MONTHLY STATS ─────────────────────────────────────────────────────────
curl -s "$BASE/api/analytics/stats/?period=monthly" \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 9. STATS — UNAUTHENTICATED ────────────────────────────────────────────────
# All analytics endpoints require authentication. Expect HTTP 401.
curl -s -o /dev/null -w "%{http_code}\n" \
  "$BASE/api/analytics/stats/"
