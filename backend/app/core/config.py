from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocTongue API"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    storage_root: Path = Path(__file__).resolve().parents[2] / "data"
    chat_audit_log_path: Path | None = None
    uploads_dir: Path | None = None
    chroma_dir: Path | None = None
    documents_manifest: Path | None = None
    chroma_collection_name: str = "documents"
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_k: int = 5
    embedding_provider: str = "local"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 256
    embedding_api_base: str | None = None
    embedding_api_key: str | None = None
    llm_provider: str = "stub"
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str | None = None
    llm_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    openrouter_api_key: str | None = None
    azure_api_key: str | None = None
    llm_temperature: float = 0.1
    llm_timeout_seconds: float = 60.0
    max_answer_citations: int = 3
    chat_memory_window: int = 3
    chat_memory_ttl_seconds: int = 3600
    redis_url: str = "redis://localhost:6379/0"
    redis_chat_key_prefix: str = "doctongue:chat"

    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[3] / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        if self.chat_audit_log_path is None:
            self.chat_audit_log_path = self.storage_root / "chat_audit.txt"
        if self.uploads_dir is None:
            self.uploads_dir = self.storage_root / "uploads"
        if self.chroma_dir is None:
            self.chroma_dir = self.storage_root / "chroma"
        if self.documents_manifest is None:
            self.documents_manifest = self.storage_root / "documents.json"

    def ensure_storage(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.chat_audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        if not self.documents_manifest.exists():
            self.documents_manifest.write_text("[]\n", encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_storage()
    return settings