from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings
from app.core.dependencies import get_answer_generator, get_vector_store, settings_dependency
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm import AnswerGenerator
from app.services.retrieval import answer_question
from app.services.vector_store import VectorStore


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    settings: Settings = Depends(settings_dependency),
    vector_store: VectorStore = Depends(get_vector_store),
    answer_generator: AnswerGenerator = Depends(get_answer_generator),
) -> ChatResponse:
    try:
        return answer_question(payload.question, settings, vector_store, answer_generator)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to answer question.") from exc