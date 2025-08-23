from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "labellerr-semantic-chatbot"
    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    NORMALIZE_EMBEDDINGS: bool = True

    # Vector DB (default to Chroma; you can switch to Qdrant later)
    CHROMA_DIR: str = "./data_ingest/vector_db"
    CHROMA_COLLECTION: str = "labellerr_content_minilm"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "updates_minilm"

    # RAG
    RAG_TOP_K: int = 5
    RAG_MAX_CONTEXT_CHARS: int = 1200

    # Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
