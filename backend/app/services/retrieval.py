from dataclasses import dataclass
import logging

from app.core.config import Settings
from app.models.schemas import ChatResponse, Citation
from app.services.llm import AnswerGenerator, lexical_overlap_score
from app.services.vector_store import SearchResult, VectorStore


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievalOutcome:
    answer: str
    citations: list[Citation]
    grounded: bool


def answer_question(
    question: str,
    settings: Settings,
    vector_store: VectorStore,
    answer_generator: AnswerGenerator,
) -> ChatResponse:
    hits = vector_store.search(question, settings.retrieval_k)
    if not hits:
        return ChatResponse(
            answer="I could not find an answer in the indexed documents.",
            citations=[],
            grounded=False,
        )

    top_hits = _filter_grounded_hits(question, hits)
    if not top_hits:
        return ChatResponse(
            answer="I could not find enough supporting evidence in the indexed documents to answer that.",
            citations=[],
            grounded=False,
        )

    grounded = True
    try:
        answer = answer_generator.generate_answer(question, [hit.content for hit in top_hits])
    except Exception as exc:
        logger.exception("LLM answer generation failed, returning evidence-only fallback.")
        answer = (
            "I found relevant excerpts in the indexed documents, but I could not generate "
            "a final response from the configured LLM provider."
        )
        grounded = False

    citations = [
        Citation(
            document_id=hit.document_id,
            filename=hit.filename,
            excerpt=hit.content,
            page_number=hit.page_number,
            score=round(hit.score, 3),
        )
        for hit in top_hits[: settings.max_answer_citations]
    ]
    return ChatResponse(answer=answer, citations=citations, grounded=grounded)


def _filter_grounded_hits(question: str, hits: list[SearchResult]) -> list[SearchResult]:
    grounded_hits: list[SearchResult] = []
    for hit in hits:
        if lexical_overlap_score(question, hit.content) >= 0.1 or hit.score >= 0.55:
            grounded_hits.append(hit)
    return grounded_hits