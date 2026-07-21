from dataclasses import dataclass
import re


@dataclass(slots=True)
class PageContent:
    text: str
    page_number: int | None = None


@dataclass(slots=True)
class TextChunk:
    content: str
    chunk_index: int
    page_number: int | None = None


def normalize_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed


def split_pages_into_chunks(
    pages: list[PageContent],
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
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