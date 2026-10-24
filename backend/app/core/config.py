from pathlib import Path
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # ── Core ─────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "TaxEase"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    # ── Existing integrations (unchanged) ────────────────────────────────────
    GEMINI_API_KEY: str = ""
    MONGODB_URL: str = ""

    # ── Qdrant vector database ───────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""                      # empty for local Docker
    QDRANT_COLLECTION: str = "income_tax_act"

    # ── Embedding model ──────────────────────────────────────────────────────
    # gemini-embedding-2 is the currently supported Gemini embedding model.
    # Do NOT use text-embedding-004 (retired).
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    # Dimension is configurable — do NOT hardcode. Verify by calling the model
    # on first use. gemini-embedding-2 supports 1..3072; default is 768.
    EMBEDDING_DIMENSION: int = 768
    EMBEDDING_BATCH_SIZE: int = 100

    # ── RAG retrieval behaviour ──────────────────────────────────────────────
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.72
    RAG_ENABLED: bool = True       # master toggle; False → graceful fallback

    # ── PDF ingestion ────────────────────────────────────────────────────────
    PDF_DATA_DIR: str = "data"
    MAX_TOKENS_PER_CHUNK: int = 400
    CHUNK_OVERLAP_TOKENS: int = 50

    class Config:
        env_file = [".env", str(_BACKEND_DIR / ".env")]

settings = Settings()
