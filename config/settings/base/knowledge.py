from .general import env

# OPENAI / Knowledge base
# ------------------------------------------------------------------------------
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_EMBEDDING_MODEL = env(
    "OPENAI_EMBEDDING_MODEL",
    default="text-embedding-3-small",
)

# text-embedding-3-small outputs 1536 dimensions
EMBEDDING_DIMENSIONS = 1536

# Word-based chunking: ~200 words per chunk, 20-word overlap
KNOWLEDGE_CHUNK_SIZE = env.int("KNOWLEDGE_CHUNK_SIZE", default=200)
KNOWLEDGE_CHUNK_OVERLAP = env.int("KNOWLEDGE_CHUNK_OVERLAP", default=20)
