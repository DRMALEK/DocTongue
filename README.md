# DocTongue-2

DocTongue is a simple full-stack document Q&A application. Users upload PDFs or text files into a shared collection, ask questions in a chat-style interface, and receive answers grounded only in retrieved document content with visible supporting evidence.

## Stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4
- Backend: FastAPI, Python 3.12
- Document parsing: PyPDF
- Retrieval: local chunking, embeddings, ChromaDB vector search
- LLM integration: provider-agnostic answer generation through LiteLLM, with a local stub mode for zero-key local development

## Features

- Upload and process PDFs, TXT, and Markdown files
- Search across multiple documents in a single shared collection
- Chat-style grounded Q&A
- Visible citations with filename, page number, excerpt, and score
- Document listing and deletion
- Basic backend tests for chunking and API flows

## Architecture

The repository is split into two applications:

- `frontend/`: the Next.js interface for document upload, collection management, and chat
- `backend/`: the FastAPI service that handles ingestion, chunking, embeddings, Chroma persistence, retrieval, and answer generation

### Backend flow

1. A file upload hits `POST /api/documents`.
2. The backend validates the file type and size, stores the original file locally, and extracts readable text.
3. Extracted text is chunked with overlap and embedded.
4. Chunks and metadata are stored in ChromaDB.
5. A chat question hits `POST /api/chat`.
6. The question is embedded, relevant chunks are retrieved, and the answer generator returns a grounded answer.
7. The API returns the answer plus citations for UI rendering.

### Grounding behavior

- Retrieval is limited to indexed documents only.
- Answers include explicit supporting evidence cards in the UI.
- If retrieval does not provide enough support, the backend returns a grounded fallback instead of guessing.

## Repository structure

See `project-structure.txt` for the concise file organization.

## Environment variables

Copy `.env.example` to `.env` at the repository root and adjust values as needed.

For local development in a dev container, leave `NEXT_PUBLIC_API_BASE_URL` empty and use `BACKEND_API_BASE_URL=http://127.0.0.1:8000` so the Next.js dev server proxies browser requests to FastAPI.

### Important defaults

- `LLM_PROVIDER=stub` keeps local development simple and does not require API keys.
- `EMBEDDING_PROVIDER=local` uses a local hashed embedding strategy for retrieval.
- To use a real model provider, set `LLM_PROVIDER` and `EMBEDDING_PROVIDER` to `litellm`, choose model names, and export the matching provider keys.
- `LLM_API_BASE`, `LLM_API_KEY`, `EMBEDDING_API_BASE`, and `EMBEDDING_API_KEY` are optional overrides for OpenAI-compatible or proxy endpoints.
- `LLM_TIMEOUT_SECONDS` controls both live embedding and completion request timeouts.

## Local setup

### 1. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000`.
Its `/api/*` requests are proxied by Next.js to `BACKEND_API_BASE_URL`.

### 2. Backend

```bash
cd backend
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The backend runs on `http://localhost:8000`.

## API summary

### `GET /api/documents`

Returns the indexed document list.

### `POST /api/documents`

Accepts a multipart file upload and indexes one document.

### `DELETE /api/documents/{document_id}`

Deletes a document from local storage and the vector store.

### `POST /api/chat`

Accepts a JSON body like:

```json
{
	"question": "Where are uploaded documents stored?"
}
```

Returns a grounded answer and citation list.

## Testing

### Backend

```bash
cd backend
pytest -q
```

### Live LiteLLM smoke test

This smoke test is skipped by default. It is only intended for an explicit real-provider check.

```bash
cd backend
RUN_LIVE_LLM_SMOKE_TEST=1 \
LLM_PROVIDER=litellm \
EMBEDDING_PROVIDER=litellm \
pytest -q -k live_litellm_smoke
```

Provide matching model names and credentials through `.env` or exported environment variables before running it.

### Frontend

```bash
cd frontend
npm test
npm run lint
npm run build
```

## Notes

- Uploaded files and Chroma data are stored under `backend/data/` and ignored by Git.
- The current app uses one shared collection in v1.
- Scanned PDFs without extractable text are not OCR-processed in this version.