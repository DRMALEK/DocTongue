from collections import Counter
import math
import re

from litellm import completion, embedding

from app.core.config import Settings


TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
LITELLM_PROVIDER_ALIASES = {
    "litellm",
    "openai",
    "anthropic",
    "gemini",
    "openrouter",
    "azure",
}


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if _uses_litellm_provider(self._settings.embedding_provider):
            model = _normalize_model_name(
                provider=self._settings.embedding_provider,
                model=self._settings.embedding_model,
            )
            response = embedding(
                model=model,
                input=texts,
                **_build_litellm_kwargs(
                    api_base=self._settings.embedding_api_base,
                    api_key=_resolve_api_key(
                        self._settings.embedding_provider,
                        self._settings.embedding_api_key,
                        self._settings,
                    ),
                    timeout=self._settings.llm_timeout_seconds,
                ),
            )
            return [item["embedding"] for item in response.data]
        if self._settings.embedding_provider != "local":
            raise ValueError(
                f"Unsupported embedding provider: {self._settings.embedding_provider}"
            )
        return [_hashed_embedding(text, self._settings.embedding_dimensions) for text in texts]


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_answer(self, question: str, contexts: list[str]) -> str:
        if self._settings.llm_provider == "stub":
            return _fallback_answer(question, contexts)
        if not _uses_litellm_provider(self._settings.llm_provider):
            raise ValueError(f"Unsupported LLM provider: {self._settings.llm_provider}")

        model = _normalize_model_name(
            provider=self._settings.llm_provider,
            model=self._settings.llm_model,
        )

        prompt_context = "\n\n".join(
            f"Source {index + 1}:\n{context}"
            for index, context in enumerate(contexts)
        )
        response = completion(
            model=model,
            temperature=self._settings.llm_temperature,
            **_build_litellm_kwargs(
                api_base=self._settings.llm_api_base,
                api_key=_resolve_api_key(
                    self._settings.llm_provider,
                    self._settings.llm_api_key,
                    self._settings,
                ),
                timeout=self._settings.llm_timeout_seconds,
            ),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from the provided document excerpts. "
                        "Cite every factual claim with source markers like [1] or [2], "
                        "where numbers map to the provided Source blocks. "
                        "If the answer is not supported, say you could not find it in the indexed documents."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext:\n{prompt_context}",
                },
            ],
        )
        return response.choices[0].message.content.strip()


def _build_litellm_kwargs(
    *,
    api_base: str | None,
    api_key: str | None,
    timeout: float,
) -> dict[str, str | float]:
    kwargs: dict[str, str | float] = {"timeout": timeout}
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    return kwargs


def _uses_litellm_provider(provider: str) -> bool:
    return provider in LITELLM_PROVIDER_ALIASES


def _resolve_api_key(provider: str, explicit_api_key: str | None, settings: Settings) -> str | None:
    if explicit_api_key:
        return explicit_api_key
    if provider in {"litellm", "openai", "azure"}:
        return settings.openai_api_key or settings.azure_api_key
    if provider == "anthropic":
        return settings.anthropic_api_key
    if provider == "gemini":
        return settings.gemini_api_key
    if provider == "openrouter":
        return settings.openrouter_api_key
    return None


def _normalize_model_name(provider: str, model: str) -> str:
    if provider == "litellm" or "/" in model:
        return model
    return f"{provider}/{model}"


def _hashed_embedding(text: str, dimensions: int) -> list[float]:
    counts = Counter(token.lower() for token in TOKEN_RE.findall(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        index = hash(token) % dimensions
        vector[index] += float(count)
    return _normalize_vector(vector)


def _normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _fallback_answer(question: str, contexts: list[str]) -> str:
    if not contexts:
        return "I could not find an answer in the indexed documents."
    lead = contexts[0]
    if len(contexts) == 1:
        return f"Based on the indexed documents: {lead} [1]"
    supporting = contexts[1]
    return (
        "Based on the indexed documents, the most relevant evidence is: "
        f"{lead} [1] Additional supporting context: {supporting} [2]"
    )


def lexical_overlap_score(question: str, text: str) -> float:
    question_terms = {token.lower() for token in TOKEN_RE.findall(question)}
    context_terms = {token.lower() for token in TOKEN_RE.findall(text)}
    if not question_terms or not context_terms:
        return 0.0
    return len(question_terms & context_terms) / len(question_terms)