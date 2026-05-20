#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Notification Preferences API — smoke tests
# ---------------------------------------------------------------------------
# Prerequisites:
#   - Server running at BASE_URL
#   - Valid JWT access token in $TOKEN
#   - User has a company profile
#
# Usage:
#   export BASE_URL=http://localhost:8000
#   export TOKEN=<your_jwt_access_token>
#   bash test.sh
# ---------------------------------------------------------------------------

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH="Authorization: Bearer $TOKEN"

echo "=== 1. GET /api/notifications/preferences/me/ (auto-creates defaults) ==="
curl -s -X GET "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Accept: application/json" | python3 -m json.tool

echo ""
echo "=== 2. PATCH /api/notifications/preferences/me/ — disable operator handoff ==="
curl -s -X PATCH "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"notify_on_operator_handoff": false}' | python3 -m json.tool

echo ""
echo "=== 3. PATCH /api/notifications/preferences/me/ — set threshold to 60 minutes ==="
curl -s -X PATCH "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"unanswered_threshold_minutes": 60}' | python3 -m json.tool

echo ""
echo "=== 4. PATCH /api/notifications/preferences/me/ — set override email ==="
curl -s -X PATCH "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"notification_email": "alerts@example.com"}' | python3 -m json.tool

echo ""
echo "=== 5. PATCH /api/notifications/preferences/me/ — disable weekly summary ==="
curl -s -X PATCH "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"weekly_summary": false}' | python3 -m json.tool

echo ""
echo "=== 6. GET /api/notifications/preferences/me/ — verify final state ==="
curl -s -X GET "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Accept: application/json" | python3 -m json.tool

echo ""
echo "=== 7. PATCH — restore defaults ==="
curl -s -X PATCH "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "notify_on_operator_handoff": true,
    "notify_on_unanswered": true,
    "unanswered_threshold_minutes": 30,
    "weekly_summary": true,
    "notification_email": ""
  }' | python3 -m json.tool

echo ""
echo "=== 8. PATCH — invalid threshold (negative) — expect 400 ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH \
  "$BASE_URL/api/notifications/preferences/me/" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"unanswered_threshold_minutes": -5}')
echo "HTTP $STATUS (expected 400)"

echo ""
echo "=== 9. GET without auth — expect 401 ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/notifications/preferences/me/")
echo "HTTP $STATUS (expected 401)"

echo ""
echo "All tests complete."
