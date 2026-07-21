import os

import pytest

from app.core.config import Settings
from app.services.llm import AnswerGenerator, EmbeddingService


def test_live_litellm_smoke() -> None:
    if os.getenv("RUN_LIVE_LLM_SMOKE_TEST") != "1":
        pytest.skip("Set RUN_LIVE_LLM_SMOKE_TEST=1 to run the live LiteLLM smoke test.")

    settings = Settings()
    if settings.llm_provider != "litellm" or settings.embedding_provider != "litellm":
        pytest.skip(
            "Set LLM_PROVIDER=litellm and EMBEDDING_PROVIDER=litellm before running the live smoke test."
        )

    embeddings = EmbeddingService(settings).embed_texts(
        ["DocTongue uses retrieved document evidence to answer questions."]
    )
    assert len(embeddings) == 1
    assert embeddings[0]

    answer = AnswerGenerator(settings).generate_answer(
        question="How does DocTongue answer questions?",
        contexts=["DocTongue uses retrieved document evidence to answer questions."],
    )
    assert answer.strip()