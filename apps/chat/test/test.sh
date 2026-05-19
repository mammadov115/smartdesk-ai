BASE=http://localhost:8000

# ── PREREQUISITE: LOGIN  →  save access token ─────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"StrongPass1!"}' | jq

# Store the access token for subsequent requests:
ACCESS=<paste access token here>

# ── 1. CREATE A CHAT SESSION ──────────────────────────────────────────────────
# Returns the session ID, the AI's display name, and the greeting message
# (both pulled from the user's CompanyProfile chat settings).
curl -s -X POST $BASE/api/chat/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" | jq

# Store the returned session id:
SESSION_ID=<paste session id here>

# ── 2. LIST SESSIONS ──────────────────────────────────────────────────────────
curl -s $BASE/api/chat/sessions/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 3. RETRIEVE A SESSION ─────────────────────────────────────────────────────
curl -s $BASE/api/chat/sessions/$SESSION_ID/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 4. ASK A QUESTION  (RAG pipeline) ────────────────────────────────────────
# The backend will:
#   1. Embed the question (OpenAI text-embedding-3-small)
#   2. Cosine-search pgvector for relevant chunks owned by this user
#   3. If no chunks pass the similarity threshold → fallback reply
#   4. Otherwise build a prompt and call gpt-4o-mini via LangChain
#   5. Persist both the user turn and the assistant turn
# Response contains: role, content, sources ([{document_id, title}]), created_at
curl -s -X POST $BASE/api/chat/sessions/$SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"What is your refund policy?"}' | jq

# ── 5. ASK ANOTHER QUESTION ───────────────────────────────────────────────────
curl -s -X POST $BASE/api/chat/sessions/$SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"How do I reset my password?"}' | jq

# ── 6. FALLBACK — question with no matching knowledge ─────────────────────────
# If no document chunk is within the similarity threshold (0.7 cosine distance),
# the answer will be: "I don't know, you'll be connected to an operator."
# sources will be an empty list.
curl -s -X POST $BASE/api/chat/sessions/$SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"What is the weather on Mars?"}' | jq

# ── 7. GET FULL MESSAGE HISTORY FOR A SESSION ─────────────────────────────────
# Returns all turns in chronological order (user + assistant alternating).
# Each assistant message includes the sources list used to generate the answer.
curl -s $BASE/api/chat/sessions/$SESSION_ID/messages/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 8. READ CURRENT CHAT SETTINGS ────────────────────────────────────────────
# chat_name, greeting_message, and chat_language are returned together with the
# rest of the CompanyProfile fields.
curl -s $BASE/api/company/me/ \
  -H "Authorization: Bearer $ACCESS" | jq

# ── 9. UPDATE CHAT SETTINGS (select language) ────────────────────────────────
# PATCH is partial — only the fields you send are changed.
# After this, every new LLM call will include "Always respond in Azerbaijani."
# in the system prompt.
curl -s -X PATCH $BASE/api/company/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{
    "chat_name": "Asistan",
    "greeting_message": "Salam! Sizə necə kömək edə bilərəm?",
    "chat_language": "Azerbaijani"
  }' | jq

# ── 10. VERIFY — ask again and check the reply language ──────────────────────
# The assistant should now respond in Azerbaijani.
curl -s -X POST $BASE/api/chat/sessions/$SESSION_ID/ask/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"question":"What services do you offer?"}' | jq

# ── 11. RESET LANGUAGE TO DEFAULT ────────────────────────────────────────────
# Send an empty string to remove the language instruction from the system prompt.
curl -s -X PATCH $BASE/api/company/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"chat_language": ""}' | jq
