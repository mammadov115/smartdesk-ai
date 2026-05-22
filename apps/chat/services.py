import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pgvector.django import CosineDistance

from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

FALLBACK_ANSWER = "I don't know, you'll be connected to an operator."


def answer_question(question: str, owner_user, company_profile) -> dict:
    """
    RAG pipeline:
      1. Resolve company chat settings (must happen before any early return).
      2. Embed the question via OpenAI Embeddings (LangChain).
      3. Search pgvector for the most similar chunks owned by `owner_user`.
      4. If nothing passes the similarity threshold → return fallback (translated
         via LLM when chat_language is set, otherwise hardcoded English).
      5. Build a prompt with the retrieved context and invoke the LLM (LangChain).
      6. Return {"answer": str, "sources": [{"document_id": int, "title": str}, ...]}.
    """
    # 1. Resolve company chat settings up front so every code path can use them
    chat_name = getattr(company_profile, "chat_name", "AI Assistant") if company_profile else "AI Assistant"
    chat_language = getattr(company_profile, "chat_language", "") if company_profile else ""
    lang_instruction = f"Always respond in {chat_language}." if chat_language else ""

    # 2. Embed the question
    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    query_vector = embeddings.embed_query(question)

    # 3. pgvector similarity search (cosine distance)
    chunks = list(
        KnowledgeChunk.objects.filter(
            document__owner=owner_user,
            document__status=KnowledgeDocument.Status.READY,
        )
        .annotate(distance=CosineDistance("embedding", query_vector))
        .filter(distance__lt=settings.CHAT_SIMILARITY_THRESHOLD)
        .order_by("distance")
        .select_related("document")[: settings.CHAT_TOP_K]
    )

    # 4. Fallback when no relevant context was found
    if not chunks:
        logger.debug(
            "No relevant chunks found for question %r (owner=%s). Returning fallback.",
            question,
            owner_user.pk,
        )
        if not lang_instruction:
            return {"answer": FALLBACK_ANSWER, "sources": [], "is_fallback": True, "embedding": query_vector}

        # Translate the fallback message through the LLM so it respects chat_language
        fallback_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", f"You are a helpful assistant named {chat_name}. {lang_instruction}"),
                (
                    "human",
                    "You have no relevant information to answer the user's question. "
                    "In one sentence, politely tell the user you don't know and that "
                    "they will be connected to a human operator.",
                ),
            ]
        )
        fallback_llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
        )
        fallback_answer = (fallback_prompt | fallback_llm | StrOutputParser()).invoke({})
        return {"answer": fallback_answer, "sources": [], "is_fallback": True, "embedding": query_vector}

    # 5. Build context string and deduplicated source list
    context = "\n\n".join(chunk.content for chunk in chunks)
    seen: dict[int, str] = {}
    for chunk in chunks:
        if chunk.document_id not in seen:
            seen[chunk.document_id] = chunk.document.title
    sources = [{"document_id": doc_id, "title": title} for doc_id, title in seen.items()]

    # 6. Build prompt — inject company chat settings
    system_prompt = (
        f"You are a helpful assistant named {chat_name}. "
        "Answer the user's question based only on the provided context. "
        "If the context does not contain enough information to answer, say so clearly. "
        f"{lang_instruction}"
    ).strip()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )

    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_CHAT_MODEL,
        temperature=0,
    )

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})

    return {"answer": answer, "sources": sources, "is_fallback": False, "embedding": query_vector}


def escalate_to_operator(session) -> None:
    """
    Transition a ChatSession from AI mode to WAITING and broadcast an
    escalation notification to the operators_room channel group so that
    any connected operator dashboards are alerted in real time.
    """
    from .models import ChatSession  # local import to avoid circular at module level

    session.status = ChatSession.Status.WAITING
    session.save(update_fields=["status", "updated_at"])

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "operators_room",
        {
            "type": "escalation.notification",
            "session_id": session.pk,
            "owner_email": session.owner.email,
        },
    )
    logger.info("Session %s escalated to operator (owner=%s)", session.pk, session.owner.email)

    # Queue the operator handoff email notification (deferred import avoids
    # any potential circular dependency at module load time).
    try:
        from apps.notifications.tasks import notify_operator_handoff
        notify_operator_handoff.delay(session.pk)
    except Exception:
        logger.exception(
            "Failed to queue operator handoff notification for session %s", session.pk
        )


# ---------------------------------------------------------------------------
# Session creation helpers (billing coordination)
# ---------------------------------------------------------------------------

def check_session_creation_allowed(user) -> None:
    """Raise ValidationError if the user's company has hit its monthly conversation limit."""
    company = getattr(user, "company_profile", None)
    if company:
        from apps.billing.services import check_conversation_limit
        check_conversation_limit(company)


def record_session_created(user) -> None:
    """Increment the monthly conversation counter after a session is persisted."""
    company = getattr(user, "company_profile", None)
    if company:
        from apps.billing.services import increment_conversations
        increment_conversations(company)


# ---------------------------------------------------------------------------
# Ask / RAG orchestration
# ---------------------------------------------------------------------------

def handle_ask(session, question: str, user) -> "ChatMessage":  # type: ignore[name-defined]
    """
    Orchestrate a single ask-answer cycle:
      1. Persist the user message.
      2. Run the RAG pipeline (with graceful fallback on error).
      3. Persist the question embedding for analytics clustering.
      4. Persist the assistant message.
      5. Escalate to operator on the first fallback in this session.

    Returns the assistant ChatMessage instance.
    """
    from .models import ChatMessage, ChatSession  # local import avoids circular at module level

    user_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=question,
    )

    company_profile = getattr(user, "company_profile", None)

    try:
        result = answer_question(question, user, company_profile)
    except Exception:
        logger.exception("RAG pipeline error for session %s", session.pk)
        result = {"answer": FALLBACK_ANSWER, "sources": [], "is_fallback": True}

    if result.get("embedding") is not None:
        user_msg.embedding = result["embedding"]
        user_msg.save(update_fields=["embedding"])

    assistant_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=result["answer"],
        sources=result["sources"],
    )

    if result.get("is_fallback") and session.status == ChatSession.Status.AI:
        from apps.billing.services import is_operator_allowed
        if is_operator_allowed(company_profile):
            try:
                escalate_to_operator(session)
            except Exception:
                logger.exception("Failed to escalate session %s to operator", session.pk)
        else:
            logger.debug(
                "Operator escalation skipped for session %s — free plan.", session.pk
            )

    return assistant_msg
