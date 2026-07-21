from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class DocumentSummary(BaseModel):
    id: str
    filename: str
    content_type: str
    page_count: int
    chunk_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentUploadResponse(BaseModel):
    document: DocumentSummary


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str


class Citation(BaseModel):
    document_id: str
    filename: str
    excerpt: str
    page_number: int | None = None
    score: float = Field(ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=128)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
