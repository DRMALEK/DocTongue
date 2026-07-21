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


class MarkerAnswerGenerator:
    def __init__(self, answer: str) -> None:
        self._answer = answer

    def generate_answer(self, question: str, contexts: list[str]) -> str:
        return self._answer


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


def test_answer_question_binds_citations_to_referenced_sources() -> None:
    settings = Settings(max_answer_citations=3)
    vector_store = StubVectorStore(
        [
            SearchResult(
                document_id="doc-1",
                filename="policy-a.txt",
                content="Expense reports are due by Friday.",
                page_number=1,
                score=0.92,
            ),
            SearchResult(
                document_id="doc-2",
                filename="policy-b.txt",
                content="Retention policy keeps records for seven years.",
                page_number=2,
                score=0.89,
            ),
        ]
    )

    response = answer_question(
        question="What is the retention policy?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=MarkerAnswerGenerator(
            "The retention policy keeps records for seven years. [2]"
        ),
    )

    assert response.grounded is True
    assert len(response.citations) == 1
    assert response.citations[0].document_id == "doc-2"
    assert response.citations[0].filename == "policy-b.txt"


def test_answer_question_deduplicates_citations_by_document() -> None:
    settings = Settings(max_answer_citations=3)
    vector_store = StubVectorStore(
        [
            SearchResult(
                document_id="doc-1",
                filename="interview-options.txt",
                content="Option A: Chat with your docs.",
                page_number=1,
                score=0.95,
            ),
            SearchResult(
                document_id="doc-1",
                filename="interview-options.txt",
                content="Option B: Code documentation assistant.",
                page_number=1,
                score=0.92,
            ),
            SearchResult(
                document_id="doc-2",
                filename="guidelines.txt",
                content="Choose the option that excites you most.",
                page_number=2,
                score=0.9,
            ),
        ]
    )

    response = answer_question(
        question="What are the interview project options?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=MarkerAnswerGenerator(
            "Available options include chat with docs [1], code documentation assistant [2], and guidance [3]."
        ),
    )

    assert response.grounded is True
    assert len(response.citations) == 2
    assert response.citations[0].document_id == "doc-1"
    assert response.citations[1].document_id == "doc-2"
    assert "[2]" in response.answer


def test_answer_question_normalizes_markers_for_same_document() -> None:
    settings = Settings(max_answer_citations=3)
    vector_store = StubVectorStore(
        [
            SearchResult(
                document_id="doc-1",
                filename="interview-options.txt",
                content="Option A: Chat with your docs.",
                page_number=1,
                score=0.95,
            ),
            SearchResult(
                document_id="doc-1",
                filename="interview-options.txt",
                content="Option B: Code documentation assistant.",
                page_number=1,
                score=0.92,
            ),
        ]
    )

    response = answer_question(
        question="What are the interview project options?",
        settings=settings,
        vector_store=vector_store,
        answer_generator=MarkerAnswerGenerator("Options include A and B [1][2]."),
    )

    assert response.grounded is True
    assert len(response.citations) == 1
    assert response.citations[0].document_id == "doc-1"
    assert "[1][2]" not in response.answer
    assert "[1]." in response.answer or "[1]" in response.answer