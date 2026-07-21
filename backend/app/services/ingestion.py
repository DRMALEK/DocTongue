from dataclasses import dataclass
from pathlib import Path
import uuid

from fastapi import UploadFile
from pypdf import PdfReader

from app.core.config import Settings
from app.services.chunking import PageContent, TextChunk, split_pages_into_chunks


SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class DocumentProcessingError(Exception):
    pass


@dataclass(slots=True)
class ProcessedDocument:
    document_id: str
    filename: str
    content_type: str
    stored_path: Path
    page_count: int
    chunks: list[TextChunk]


async def persist_and_process_upload(
    file: UploadFile,
    settings: Settings,
) -> ProcessedDocument:
    filename = (file.filename or "").strip()
    if not filename:
        raise DocumentProcessingError("Uploaded files must include a filename.")

    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentProcessingError("Unsupported file type. Upload a PDF, TXT, or MD file.")

    payload = await file.read()
    if not payload:
        raise DocumentProcessingError("The uploaded file is empty.")

    document_id = str(uuid.uuid4())
    stored_name = f"{document_id}{extension}"
    stored_path = settings.uploads_dir / stored_name
    stored_path.write_bytes(payload)

    try:
        pages = _extract_pages(stored_path, extension)
    except Exception as exc:
        if stored_path.exists():
            stored_path.unlink()
        raise DocumentProcessingError(f"Failed to parse document: {exc}") from exc

    chunks = split_pages_into_chunks(pages, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        if stored_path.exists():
            stored_path.unlink()
        raise DocumentProcessingError("No readable text was found in the uploaded document.")

    return ProcessedDocument(
        document_id=document_id,
        filename=filename,
        content_type=SUPPORTED_EXTENSIONS[extension],
        stored_path=stored_path,
        page_count=max(len(pages), 1),
        chunks=chunks,
    )


def delete_stored_file(path: Path) -> None:
    if path.exists():
        path.unlink()


def _extract_pages(path: Path, extension: str) -> list[PageContent]:
    if extension == ".pdf":
        reader = PdfReader(str(path))
        pages: list[PageContent] = []
        for index, page in enumerate(reader.pages, start=1):
            pages.append(PageContent(text=page.extract_text() or "", page_number=index))
        return pages

    text = path.read_text(encoding="utf-8")
    return [PageContent(text=text, page_number=1)]