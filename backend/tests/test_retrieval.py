from app.core.config import Settings
from app.services.llm import AnswerGenerator
from app.services.retrieval import answer_question
from app.services.vector_store import SearchResult


class StubVectorStore:
    def __init__(self, hits: list[SearchResult]) -> None:
        self._hits = hits

    def search(self, question: str, limit: int) -> list[SearchResult]:
        return self._hits[:limit]


class FailingAnswerGenerator:
    def generate_answer(self, question: str, contexts: list[str]) -> str:
        raise RuntimeError("provider failure")


def test_answer_question_returns_not_found_when_no_hits() -> None:
    settings = Settings()
    answer_generator = AnswerGenerator(settings)
    vector_store = StubVectorStore([])

    response = answer_question(
        question="What is the retention policy?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=answer_generator,
    )

    assert response.grounded is False
    assert response.citations == []
    assert response.answer == "I could not find an answer in the indexed documents."


def test_answer_question_rejects_weak_support() -> None:
    settings = Settings()
    answer_generator = AnswerGenerator(settings)
    vector_store = StubVectorStore(
        [
            SearchResult(
                document_id="doc-1",
                filename="guide.txt",
                content="Orange orchard harvest timing and irrigation details.",
                page_number=1,
                score=0.2,
            )
        ]
    )

    response = answer_question(
        question="What is the employee expense reimbursement deadline?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=answer_generator,
    )

    assert response.grounded is False
    assert response.citations == []
    assert (
        response.answer
        == "I could not find enough supporting evidence in the indexed documents to answer that."
    )


def test_answer_question_returns_evidence_fallback_when_llm_fails() -> None:
    settings = Settings()
    vector_store = StubVectorStore(
        [
            SearchResult(
                document_id="doc-1",
                filename="guide.txt",
                content="The retention policy keeps records for seven years.",
                page_number=2,
                score=0.8,
            )
        ]
    )

    response = answer_question(
        question="What is the retention policy?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=FailingAnswerGenerator(),
    )

    assert response.grounded is False
    assert response.citations
    assert response.citations[0].filename == "guide.txt"
    assert "could not generate" in response.answer