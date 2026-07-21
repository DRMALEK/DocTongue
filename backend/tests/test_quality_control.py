import builtins

import pytest

from app.core.config import Settings
from app.services.quality_control import ResponseQualityEvaluator


def test_quality_control_disabled_returns_none() -> None:
    evaluator = ResponseQualityEvaluator(Settings(quality_control_enabled=False))

    result = evaluator.evaluate(
        question="What is the retention policy?",
        answer="Records are kept for seven years.",
        contexts=["Records are kept for seven years."],
        grounded=True,
    )

    assert result is None


def test_quality_control_falls_back_when_deepeval_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    evaluator = ResponseQualityEvaluator(
        Settings(
            quality_control_enabled=True,
            quality_control_threshold=0.4,
            quality_control_fail_open=True,
        )
    )

    original_import = builtins.__import__

    def import_with_block(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("deepeval"):
            raise ImportError("deepeval intentionally unavailable in unit test")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_with_block)

    result = evaluator.evaluate(
        question="What is the retention policy?",
        answer="The retention policy keeps records for seven years.",
        contexts=["The retention policy keeps records for seven years."],
        grounded=True,
    )

    assert result is not None
    assert result.method == "fallback.lexical_overlap"
    assert result.score > 0.0


def test_quality_control_raises_when_fail_open_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    evaluator = ResponseQualityEvaluator(
        Settings(
            quality_control_enabled=True,
            quality_control_fail_open=False,
        )
    )

    original_import = builtins.__import__

    def import_with_block(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("deepeval"):
            raise ImportError("deepeval intentionally unavailable in unit test")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_with_block)

    with pytest.raises(ImportError):
        evaluator.evaluate(
            question="What is the retention policy?",
            answer="Records are kept for seven years.",
            contexts=["The retention policy keeps records for seven years."],
            grounded=True,
        )
