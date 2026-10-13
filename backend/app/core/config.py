from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application settings
    APP_NAME: str = "Federated Agentic Mesh"
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres@127.0.0.1:5432/federated_mesh_dev",
        description="Async SQLAlchemy database URL"
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres@127.0.0.1:5432/federated_mesh_dev",
        description="Sync SQLAlchemy database URL for Alembic migrations"
    )

    # Security & JWT
    JWT_SECRET_KEY: str = Field(
        default="mesh_super_secret_jwt_key_for_development_32_bytes_min!",
        description="Secret key for JWT generation and verification"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Ollama Local LLM Configuration
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    ANSWER_MODEL: str = "qwen3:8b"  # Verified local installed Ollama model
    OLLAMA_TIMEOUT_SECONDS: int = 120
    OLLAMA_TEMPERATURE: float = 0.1
    OLLAMA_TOP_P: float = 0.9

    # Embeddings Configuration
    # Options: local_hash, ollama, sentence_transformers, none
    EMBEDDING_PROVIDER: str = "local_hash"
    EMBEDDING_MODEL: str = "local-deterministic-384"
    EMBEDDING_DIMENSION: int = 384
    ALLOW_MODEL_DOWNLOADS: bool = False

    # Document & RAG Uploads
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]

    # Approvals & Policies
    APPROVAL_EXPIRY_MINUTES: int = 60
    PREVENT_SELF_APPROVAL: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173"
    ]


settings = Settings()
