"""Text chunking utilities for splitting PDF page content into overlapping text chunks."""

from dataclasses import dataclass
import re


@dataclass(slots=True)
class PageContent:
    """Raw text extracted from a single PDF page."""

    text: str
    page_number: int | None = None


@dataclass(slots=True)
class TextChunk:
    """A single text excerpt produced by the chunking pass."""

    content: str
    chunk_index: int
    page_number: int | None = None


def normalize_text(text: str) -> str:
    """Collapse runs of whitespace in *text* to a single space and strip leading/trailing whitespace."""
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed


def split_pages_into_chunks(
    pages: list[PageContent],
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Split a list of pages into overlapping fixed-size text chunks.

    Chunks are split at the nearest word boundary within *chunk_size* characters.
    Consecutive chunks share *chunk_overlap* characters to preserve context at boundaries.

    Args:
        pages: Ordered list of page content objects to chunk.
        chunk_size: Maximum character length of each chunk.
        chunk_overlap: Number of characters to re-include from the end of the previous chunk.

    Returns:
        Ordered list of :class:`TextChunk` objects with sequential ``chunk_index`` values.

    Raises:
        ValueError: If *chunk_size* is zero or *chunk_overlap* is out of range.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size - 1")

    chunks: list[TextChunk] = []
    chunk_index = 0

    for page in pages:
        normalized = normalize_text(page.text)
        if not normalized:
            continue

        start = 0
        text_length = len(normalized)
        while start < text_length:
            end = min(start + chunk_size, text_length)
            if end < text_length:
                boundary = normalized.rfind(" ", start, end)
                if boundary > start + max(chunk_size // 4, 1):
                    end = boundary
            content = normalized[start:end].strip()
            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                    )
                )
                chunk_index += 1
            if end >= text_length:
                break
            start = max(end - chunk_overlap, start + 1)

    return chunks