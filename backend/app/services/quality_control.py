"""Lightweight response quality control using deepeval with safe fallbacks."""

from dataclasses import dataclass

from app.core.config import Settings
from app.services.llm import lexical_overlap_score


@dataclass
class QualityEvaluation:
    """Result of a single quality evaluation pass.

    Attributes:
        score: Numeric quality score in the range [0, 1].
        passed: Whether *score* met the configured threshold.
        method: Identifier for the evaluation method used
            (e.g. ``"deepeval.answer_relevancy"`` or ``"lexical_overlap_fallback"``).
        reason: Optional human-readable explanation from the judge model.
    """

    score: float
    passed: bool
    method: str
    reason: str | None = None


class ResponseQualityEvaluator:
    """Runs a minimal quality check over model responses.

    Primary path uses deepeval's AnswerRelevancyMetric (LLM-as-judge).
    If deepeval is unavailable or fails, we can fail open and return a simple
    lexical-overlap heuristic score.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
        grounded: bool,
    ) -> QualityEvaluation | None:
        """Evaluate the quality of *answer* relative to *question* and *contexts*.

        Returns ``None`` immediately when quality control is disabled via settings.
        When deepeval is unavailable and ``quality_control_fail_open`` is ``True``,
        falls back to a lexical-overlap heuristic instead of raising.

        Args:
            question: The original user question.
            answer: The generated answer to evaluate.
            contexts: Document excerpts used to ground the answer.
            grounded: Whether the answer was produced from retrieved evidence.

        Returns:
            A :class:`QualityEvaluation` if evaluation ran, or ``None`` if disabled.

        Raises:
            Exception: Re-raises deepeval errors when ``quality_control_fail_open`` is ``False``.
        """
        if not self._settings.quality_control_enabled:
            return None

        if not grounded and not contexts:
            # Avoid scoring explicit "no evidence" fallback responses.
            return QualityEvaluation(
                score=0.0,
                passed=False,
                method="skipped",
                reason="No supporting context available for evaluation.",
            )

        threshold = self._settings.quality_control_threshold

        try:
            from deepeval.metrics import AnswerRelevancyMetric
            from deepeval.test_case import LLMTestCase

            test_case = LLMTestCase(
                input=question,
                actual_output=answer,
                retrieval_context=contexts,
            )
            metric = AnswerRelevancyMetric(threshold=threshold)
            metric.measure(test_case)

            score = float(metric.score or 0.0)
            reason = None
            if self._settings.quality_control_include_reason:
                reason = getattr(metric, "reason", None)
            return QualityEvaluation(
                score=score,
                passed=score >= threshold,
                method="deepeval.answer_relevancy",
                reason=reason,
            )
        except Exception as exc:
            if not self._settings.quality_control_fail_open:
                raise

            # Simple deterministic fallback for local/dev reliability.
            overlap = lexical_overlap_score(question, answer)
            return QualityEvaluation(
                score=overlap,
                passed=overlap >= threshold,
                method="fallback.lexical_overlap",
                reason=f"deepeval unavailable or failed: {exc}",
            )
