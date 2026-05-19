import logging

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
      1. Embed the question via OpenAI Embeddings (LangChain).
      2. Search pgvector for the most similar chunks owned by `owner_user`.
      3. If nothing passes the similarity threshold → return fallback.
      4. Build a prompt with the retrieved context and invoke the LLM (LangChain).
      5. Return {"answer": str, "sources": [{"document_id": int, "title": str}, ...]}.
    """
    # 1. Embed the question
    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    query_vector = embeddings.embed_query(question)

    # 2. pgvector similarity search (cosine distance)
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

    # 3. Fallback when no relevant context was found
    if not chunks:
        logger.debug(
            "No relevant chunks found for question %r (owner=%s). Returning fallback.",
            question,
            owner_user.pk,
        )
        return {"answer": FALLBACK_ANSWER, "sources": []}

    # 4. Build context string and deduplicated source list
    context = "\n\n".join(chunk.content for chunk in chunks)
    seen: dict[int, str] = {}
    for chunk in chunks:
        if chunk.document_id not in seen:
            seen[chunk.document_id] = chunk.document.title
    sources = [{"document_id": doc_id, "title": title} for doc_id, title in seen.items()]

    # 5. Build prompt — inject company chat settings
    chat_name = getattr(company_profile, "chat_name", "AI Assistant") if company_profile else "AI Assistant"
    chat_language = getattr(company_profile, "chat_language", "") if company_profile else ""

    lang_instruction = f"Always respond in {chat_language}." if chat_language else ""

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

    return {"answer": answer, "sources": sources}
