from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.schemas import DocumentSummary


class DocumentStore:
    def __init__(self, settings: Settings) -> None:
        self._manifest_path = settings.documents_manifest

    def list_documents(self) -> list[DocumentSummary]:
        entries = self._read_manifest()
        return [DocumentSummary.model_validate(entry) for entry in entries]

    def get_document(self, document_id: str) -> DocumentSummary | None:
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
        if not self._manifest_path.exists():
            return []
        raw = self._manifest_path.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        return json.loads(raw)

    def _write_manifest(self, entries: list[dict[str, Any]]) -> None:
        parent = Path(self._manifest_path).parent
        parent.mkdir(parents=True, exist_ok=True)
        self._manifest_path.write_text(
            json.dumps(entries, indent=2) + "\n",
            encoding="utf-8",
        )