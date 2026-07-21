from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.dependencies import (
    get_answer_generator,
    get_document_store,
    get_embedding_service,
    get_quality_evaluator,
    get_vector_store,
)
from app.main import create_app


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    storage_root = tmp_path / "data"
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")

    get_settings.cache_clear()
    get_document_store.cache_clear()
    get_embedding_service.cache_clear()
    get_answer_generator.cache_clear()
    get_quality_evaluator.cache_clear()
    get_vector_store.cache_clear()

    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_document_store.cache_clear()
    get_embedding_service.cache_clear()
    get_answer_generator.cache_clear()
    get_quality_evaluator.cache_clear()
    get_vector_store.cache_clear()