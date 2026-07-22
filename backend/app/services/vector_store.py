"""ChromaDB-backed vector store for semantic similarity search over document chunks."""

from dataclasses import dataclass

import chromadb

from app.core.config import Settings
from app.services.chunking import TextChunk
from app.services.llm import EmbeddingService


@dataclass(slots=True)
class SearchResult:
    """A single chunk returned by a similarity search.

    Attributes:
        document_id: UUID of the parent document.
        filename: Original filename of the parent document.
        content: Text content of this chunk.
        page_number: Page the chunk was extracted from, or ``None`` if unknown.
        score: Cosine similarity score in the range [0, 1] (higher is better).
    """

    document_id: str
    filename: str
    content: str
    page_number: int | None
    score: float


class VectorStore:
    """Wrapper around a ChromaDB persistent collection used for chunk storage and retrieval."""

    def __init__(self, settings: Settings) -> None:
        """Initialise the vector store, creating or opening the named Chroma collection."""
        self._settings = settings
        self._embedding_service = EmbeddingService(settings)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, document_id: str, filename: str, chunks: list[TextChunk]) -> None:
        """Embed *chunks* and upsert them into the Chroma collection.

        Each chunk is stored with its ``document_id``, ``filename``,
        ``chunk_index``, and ``page_number`` as metadata so that search
        results can be traced back to their source documents.
        """
        if not chunks:
            return
        documents = [chunk.content for chunk in chunks]
        embeddings = self._embedding_service.embed_texts(documents)
        ids = [f"{document_id}:{chunk.chunk_index}" for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number if chunk.page_number is not None else -1,
            }
            for chunk in chunks
        ]
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to *document_id* from the collection."""
        self._collection.delete(where={"document_id": document_id})

    def search(self, question: str, limit: int) -> list[SearchResult]:
        """Return the top *limit* chunks most similar to *question*.

        Returns an empty list if the collection has no documents.
        Scores are derived from cosine distance: ``score = 1 - distance``.
        """
        if self._collection.count() == 0:
            return []
        query_embedding = self._embedding_service.embed_texts([question])[0]
        response = self._collection.query(query_embeddings=[query_embedding], n_results=limit)
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]
        hits: list[SearchResult] = []
        for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
            score = max(0.0, 1.0 - float(distance))
            page_number = metadata.get("page_number")
            hits.append(
                SearchResult(
                    document_id=str(metadata["document_id"]),
                    filename=str(metadata["filename"]),
                    content=str(document),
                    page_number=None if page_number == -1 else int(page_number),
                    score=score,
                )
            )
        return hits