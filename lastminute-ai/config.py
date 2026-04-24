"""
config.py — All settings loaded from environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str | None = None
    
    # Claude models
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 1500

    # Embeddings (OpenAI)
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # Vector store
    chroma_persist_dir: str = "./chroma_db"

    # File uploads
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 20
    allowed_extensions: list[str] = ["pdf", "docx", "png", "jpg", "jpeg", "txt"]

    # RAG chunking
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_chunks: int = 5

    # App
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
