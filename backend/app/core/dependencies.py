from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.document_store import DocumentStore
from app.services.llm import AnswerGenerator, EmbeddingService
from app.services.vector_store import VectorStore


def settings_dependency() -> Settings:
    return get_settings()


@lru_cache
def get_document_store() -> DocumentStore:
    return DocumentStore(get_settings())


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(get_settings())


@lru_cache
def get_answer_generator() -> AnswerGenerator:
    return AnswerGenerator(get_settings())


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore(get_settings())