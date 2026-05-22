import io
import logging

from django.conf import settings
from openai import OpenAI

from .models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

_openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_text(document: KnowledgeDocument) -> str:
    """Return raw text from a document based on its source_type."""
    st = document.source_type

    if st == KnowledgeDocument.SourceType.TEXT:
        return document.raw_text

    if st == KnowledgeDocument.SourceType.FAQ:
        # raw_text is already formatted as "Q: ...\nA: ..." by the serializer
        return document.raw_text

    if st == KnowledgeDocument.SourceType.TXT:
        return document.file.read().decode("utf-8", errors="replace")

    if st == KnowledgeDocument.SourceType.PDF:
        from pypdf import PdfReader  # noqa: PLC0415

        reader = PdfReader(io.BytesIO(document.file.read()))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if st == KnowledgeDocument.SourceType.DOCX:
        from docx import Document as DocxDocument  # noqa: PLC0415

        doc = DocxDocument(io.BytesIO(document.file.read()))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    raise ValueError(f"Unsupported source_type: {st}")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    Chunk size and overlap are configured via settings.
    """
    size: int = settings.KNOWLEDGE_CHUNK_SIZE
    overlap: int = settings.KNOWLEDGE_CHUNK_OVERLAP

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + size])
        chunks.append(chunk)
        start += size - overlap

    return chunks


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def generate_embedding(text: str) -> list[float]:
    """Call OpenAI Embeddings API and return the embedding vector."""
    client = _get_openai_client()
    response = client.embeddings.create(
        input=text,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    return response.data[0].embedding


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def process_document(document: KnowledgeDocument) -> None:
    """
    Full pipeline: extract text → chunk → embed → persist.
    Raises on any error so the Celery task can catch and update status.
    """
    text = extract_text(document)
    if not text.strip():
        raise ValueError("No text could be extracted from the document.")

    chunks = chunk_text(text)

    chunk_objects = []
    for idx, content in enumerate(chunks):
        embedding = generate_embedding(content)
        chunk_objects.append(
            KnowledgeChunk(
                document=document,
                chunk_index=idx,
                content=content,
                embedding=embedding,
            )
        )

    # Replace any previously stored chunks atomically
    KnowledgeChunk.objects.filter(document=document).delete()
    KnowledgeChunk.objects.bulk_create(chunk_objects)
