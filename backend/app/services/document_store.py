"""JSON-file-backed document manifest store.

The manifest is a plain JSON array written to ``settings.documents_manifest``.
All reads and writes are synchronous; the file is rewritten atomically on each
mutation to minimise the window for corruption.
"""

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.schemas import DocumentSummary


class DocumentStore:
    """Persists and queries the list of indexed documents via a JSON manifest file."""

    def __init__(self, settings: Settings) -> None:
        """Initialise the store, pointing it at the manifest path from *settings*."""
        self._manifest_path = settings.documents_manifest

    def list_documents(self) -> list[DocumentSummary]:
        """Return all documents currently recorded in the manifest."""
        entries = self._read_manifest()
        return [DocumentSummary.model_validate(entry) for entry in entries]

    def get_document(self, document_id: str) -> DocumentSummary | None:
        """Return the document with *document_id*, or ``None`` if not found."""
        for entry in self._read_manifest():
            if entry["id"] == document_id:
                return DocumentSummary.model_validate(entry)
        return None

    def create_document(
        self,
        document_id: str,
        filename: str,
        content_type: str,
        page_count: int,
        chunk_count: int,
    ) -> DocumentSummary:
        """Append a new document record to the manifest and return it."""
        entries = self._read_manifest()
        record = DocumentSummary(
            id=document_id,
            filename=filename,
            content_type=content_type,
            page_count=page_count,
            chunk_count=chunk_count,
            created_at=datetime.now(UTC),
        )
        entries.append(record.model_dump(mode="json"))
        self._write_manifest(entries)
        return record

    def delete_document(self, document_id: str) -> DocumentSummary | None:
        """Remove the document with *document_id* from the manifest.

        Returns the deleted :class:`DocumentSummary`, or ``None`` if the id
        was not present.
        """
        entries = self._read_manifest()
        kept: list[dict[str, Any]] = []
        removed: dict[str, Any] | None = None
        for entry in entries:
            if entry["id"] == document_id:
                removed = entry
                continue
            kept.append(entry)
        if removed is None:
            return None
        self._write_manifest(kept)
        return DocumentSummary.model_validate(removed)

    def _read_manifest(self) -> list[dict[str, Any]]:
        """Load the raw manifest list from disk; returns an empty list if absent."""
        if not self._manifest_path.exists():
            return []
        raw = self._manifest_path.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        return json.loads(raw)

    def _write_manifest(self, entries: list[dict[str, Any]]) -> None:
        """Serialise *entries* and overwrite the manifest file on disk."""
        parent = Path(self._manifest_path).parent
        parent.mkdir(parents=True, exist_ok=True)
        self._manifest_path.write_text(
            json.dumps(entries, indent=2) + "\n",
            encoding="utf-8",
        )