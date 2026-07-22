"""LLM and embedding service wrappers.

Provides two main classes:

- :class:`EmbeddingService`: converts text into embedding vectors via LiteLLM
  or a local hash-based fallback when ``embedding_provider="local"``.
- :class:`AnswerGenerator`: generates grounded answers and reformulates
  multi-turn queries via LiteLLM or a zero-key stub for local development.

Private helpers handle provider normalisation, API key resolution, and the
hash-based local embedding strategy.
"""

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
    """Converts text into dense embedding vectors.

    When ``embedding_provider`` is set to ``"local"`` a deterministic
    hash-based bag-of-words vector is returned (no API key required).
    Any provider listed in :data:`LITELLM_PROVIDER_ALIASES` delegates to
    LiteLLM with the configured model and credentials.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise the service with application *settings*."""
        self._settings = settings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per entry in *texts*.

        Args:
            texts: Non-empty list of strings to embed.

        Returns:
            List of float vectors with length equal to ``embedding_dimensions``.

        Raises:
            ValueError: If the configured ``embedding_provider`` is not supported.
        """
        if not texts:
            return []
        if _uses_litellm_provider(self._settings.embedding_provider):
            model = _normalize_model_name(
                provider=self._settings.embedding_provider,
                model=self._settings.embedding_model,
            )
            request_kwargs = _build_litellm_kwargs(
                api_base=self._settings.embedding_api_base,
                api_key=_resolve_api_key(
                    self._settings.embedding_provider,
                    self._settings.embedding_api_key,
                    self._settings,
                ),
                timeout=self._settings.llm_timeout_seconds,
            )
            if _supports_embedding_dimensions(
                provider=self._settings.embedding_provider,
                model=model,
            ):
                request_kwargs["dimensions"] = self._settings.embedding_dimensions
            response = embedding(
                model=model,
                input=texts,
                **request_kwargs,
            )
            return [item["embedding"] for item in response.data]
        if self._settings.embedding_provider != "local":
            raise ValueError(
                f"Unsupported embedding provider: {self._settings.embedding_provider}"
            )
        return [_hashed_embedding(text, self._settings.embedding_dimensions) for text in texts]


class AnswerGenerator:
    """Generates grounded answers and reformulates queries using an LLM.

    Supports the built-in ``"stub"`` provider for zero-key local development
    and any provider in :data:`LITELLM_PROVIDER_ALIASES` for production use.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise the generator with application *settings*."""
        self._settings = settings

    def generate_answer(self, question: str, contexts: list[str]) -> str:
        """Generate an answer to *question* grounded in the provided *contexts*.

        The LLM is instructed to cite every factual claim with ``[N]`` markers
        that correspond to the source blocks passed in *contexts*.
        Falls back to :func:`_fallback_answer` when ``llm_provider="stub"``.

        Args:
            question: The user's original question.
            contexts: Ordered list of document excerpts to cite from.

        Returns:
            Answer string that may contain ``[N]`` citation markers.

        Raises:
            ValueError: If the configured ``llm_provider`` is not supported.
        """
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

    def reformulate_query(self, question: str, recent_turns: list[dict[str, str]]) -> str:
        """Rewrite *question* into a standalone retrieval query using conversation history.

        Resolves pronouns and implicit references in *question* by consulting
        *recent_turns* (most-recent first).  Returns *question* unchanged when
        the history is empty or the provider does not support reformulation.

        Args:
            question: The latest user question.
            recent_turns: Recent chat turns, each a dict with ``"question"``
                and ``"answer"`` keys, ordered most-recent first.

        Returns:
            A self-contained query string suitable for vector search.
        """
        if not recent_turns:
            return question

        ordered_history = list(reversed(recent_turns))
        if self._settings.llm_provider == "stub":
            history_parts = [
                f"Q: {turn.get('question', '')} A: {turn.get('answer', '')}".strip()
                for turn in ordered_history
            ]
            history = " ".join(part for part in history_parts if part)
            return f"{history} {question}".strip()
        if not _uses_litellm_provider(self._settings.llm_provider):
            return question

        model = _normalize_model_name(
            provider=self._settings.llm_provider,
            model=self._settings.llm_model,
        )
        history_lines: list[str] = []
        for index, turn in enumerate(ordered_history):
            history_lines.append(
                f"Turn {index + 1} User: {turn.get('question', '').strip()}"
            )
            history_lines.append(
                f"Turn {index + 1} Assistant: {turn.get('answer', '').strip()}"
            )
        history_block = "\n".join(history_lines)
        response = completion(
            model=model,
            temperature=0,
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
                        "Rewrite the latest user question into a standalone retrieval query. "
                        "Use conversation history, including assistant answers, only to resolve references. "
                        "Keep it concise and return only the rewritten query text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Recent conversation turns (oldest to newest):\n"
                        f"{history_block}\n\n"
                        f"Current user question: {question}"
                    ),
                },
            ],
        )
        rewritten = response.choices[0].message.content.strip()
        return rewritten or question


def _build_litellm_kwargs(
    *,
    api_base: str | None,
    api_key: str | None,
    timeout: float,
) -> dict[str, str | float | int]:
    """Build optional keyword arguments for a LiteLLM ``completion``/``embedding`` call."""
    kwargs: dict[str, str | float | int] = {"timeout": timeout}
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    return kwargs


def _supports_embedding_dimensions(provider: str, model: str) -> bool:
    """Return ``True`` when provider/model pair supports a ``dimensions`` override."""
    if provider not in {"openai", "azure"}:
        return False
    normalized = model.lower()
    if "/" in normalized:
        normalized = normalized.split("/", maxsplit=1)[1]
    return normalized.startswith("text-embedding-3")


def _uses_litellm_provider(provider: str) -> bool:
    """Return ``True`` if *provider* is a recognised LiteLLM provider alias."""
    return provider in LITELLM_PROVIDER_ALIASES


def _resolve_api_key(provider: str, explicit_api_key: str | None, settings: Settings) -> str | None:
    """Determine the API key to use for *provider*, preferring *explicit_api_key* if given."""
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
    """Return the fully-qualified model name expected by LiteLLM (e.g. ``openai/gpt-4o-mini``)."""
    if provider == "litellm" or "/" in model:
        return model
    return f"{provider}/{model}"


def _hashed_embedding(text: str, dimensions: int) -> list[float]:
    """Produce a normalised hash-based bag-of-words embedding for *text*.

    Tokens are mapped into a *dimensions*-dimensional vector by hashing;
    counts are accumulated per bucket, then L2-normalised.
    """
    counts = Counter(token.lower() for token in TOKEN_RE.findall(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        index = hash(token) % dimensions
        vector[index] += float(count)
    return _normalize_vector(vector)


def _normalize_vector(vector: list[float]) -> list[float]:
    """Return *vector* scaled to unit length; return it unchanged if its norm is zero."""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _fallback_answer(question: str, contexts: list[str]) -> str:
    """Construct a simple template answer from *contexts* when no LLM is available."""
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
    """Return the fraction of *question* tokens that also appear in *text*.

    Used as a lightweight grounding check and quality-control fallback.
    Returns ``0.0`` when either string contains no alphanumeric tokens.
    """
    question_terms = {token.lower() for token in TOKEN_RE.findall(question)}
    context_terms = {token.lower() for token in TOKEN_RE.findall(text)}
    if not question_terms or not context_terms:
        return 0.0
    return len(question_terms & context_terms) / len(question_terms)