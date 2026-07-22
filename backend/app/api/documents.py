"""Documents API router: GET/POST /api/documents and DELETE /api/documents/{id}.

Handles document listing, PDF upload with ingestion, and document deletion
including cleanup from the vector store and local filesystem.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import Settings
from app.core.dependencies import get_document_store, get_vector_store, settings_dependency
from app.models.schemas import DeleteDocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.services.document_store import DocumentStore
from app.services.ingestion import DocumentProcessingError, delete_stored_file, persist_and_process_upload
from app.services.vector_store import VectorStore


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(document_store: DocumentStore = Depends(get_document_store)) -> DocumentListResponse:
    """Return the list of all currently indexed documents."""
    documents = sorted(document_store.list_documents(), key=lambda item: item.created_at, reverse=True)
    return DocumentListResponse(documents=documents)


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(settings_dependency),
    document_store: DocumentStore = Depends(get_document_store),
    vector_store: VectorStore = Depends(get_vector_store),
) -> DocumentUploadResponse:
    """Upload a PDF file, chunk it, embed the chunks, and register it in the collection.

    Returns HTTP 400 for invalid files and HTTP 422 if processing fails.
    """
    try:
        processed = await persist_and_process_upload(file, settings)
        vector_store.add_document(processed.document_id, processed.filename, processed.chunks)
        document = document_store.create_document(
            document_id=processed.document_id,
            filename=processed.filename,
            content_type=processed.content_type,
            page_count=processed.page_count,
            chunk_count=len(processed.chunks),
        )
        return DocumentUploadResponse(document=document)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to index document.") from exc


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: str,
    settings: Settings = Depends(settings_dependency),
    document_store: DocumentStore = Depends(get_document_store),
    vector_store: VectorStore = Depends(get_vector_store),
) -> DeleteDocumentResponse:
    removed = document_store.delete_document(document_id)
    if removed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    vector_store.delete_document(document_id)

    for candidate in settings.uploads_dir.glob(f"{document_id}.*"):
        delete_stored_file(Path(candidate))

    return DeleteDocumentResponse(deleted=True, document_id=document_id)