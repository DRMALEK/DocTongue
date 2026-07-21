# DocTongue

DocTongue is a simple full-stack document Q&A application. Users upload PDFs into a shared collection, ask questions in a chat-style interface, and receive answers grounded only in retrieved document content with visible supporting evidence.

![DocTongue app screenshot](Screenshot%202026-07-21%20175709.png)

## Features

- Upload and process PDF files (max 50 MB per file)
- Search across multiple documents in a single shared collection
- Chat-style grounded Q&A
- Sliding window chat memory (last 3 chat turns with question and answer) with query reformulation before retrieval
- Plain-text chat audit logging with timestamp, question, and answer saved to `backend/data/chat_audit.txt`
- Visible citations with filename only
- Input guardrails for prompt-injection attempts and restricted explicit sexual content
- Document listing and deletion
- Basic backend tests for chunking and API flows

## Stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4
- Backend: FastAPI, Python 3.12
- Document parsing: PyPDF
- Retrieval: local chunking, embeddings, ChromaDB vector search
- Chat memory: Redis (in-memory) with automatic in-process fallback when Redis is unavailable
- LLM integration: provider-agnostic answer generation through LiteLLM, with a local stub mode for zero-key local development
- Optional response quality control with deepeval (LLM-as-judge) and a safe lexical fallback

## Architecture

The repository is split into two applications:

- `frontend/`: the Next.js interface for document upload, collection management, and chat
- `backend/`: the FastAPI service that handles ingestion, chunking, embeddings, Chroma persistence, retrieval, and answer generation


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
- `QUALITY_CONTROL_ENABLED` toggles response quality evaluation for grounded answers.
- `QUALITY_CONTROL_THRESHOLD` defines pass/fail score cutoff for quality checks (0.0-1.0).
- `QUALITY_CONTROL_FAIL_OPEN` keeps chat responses flowing when judge evaluation fails and uses a local fallback score.
- `QUALITY_CONTROL_INCLUDE_REASON` includes judge/fallback reason text in API responses.
- `CHAT_MEMORY_WINDOW` controls how many recent chat turns are kept per chat session (default `3`).
- `CHAT_MEMORY_TTL_SECONDS` sets optional expiration for each session memory key in Redis.
- `REDIS_URL` and `REDIS_CHAT_KEY_PREFIX` configure where chat memory is stored.
- `CHAT_AUDIT_LOG_PATH` optionally overrides the plain-text audit log file path.

### Sliding Window Buffer with Query Reformulation

DocTongue uses a lightweight conversational memory pattern for retrieval:

1. For each chat request, the backend reads up to the last `CHAT_MEMORY_WINDOW` chat turns (question and answer pairs) from Redis using `session_id`.
2. The current question is reformulated into a standalone retrieval query using that short turn history.
3. Retrieval runs on the reformulated query, while answer generation still responds to the original current question.
4. The current question and generated answer are appended back into memory and the window is trimmed to the configured size.

If Redis is not running, the backend falls back to an in-process memory store so local development still works.

Each completed chat is also appended to a plain-text audit log with its timestamp, question, and answer. By default, that file is stored at `backend/data/chat_audit.txt`.

### Quality control (deepeval)

DocTongue now supports a simple quality control step after answer generation.

How it works:

1. The app generates a grounded answer and citations as usual.
2. If `QUALITY_CONTROL_ENABLED=1`, backend runs deepeval `AnswerRelevancyMetric` against:
	- input question
	- generated answer
	- retrieved citation context
3. The API returns `quality_control` with:
	- `score` (0.0-1.0)
	- `passed` (`score >= QUALITY_CONTROL_THRESHOLD`)
	- `method` (for example `deepeval.answer_relevancy`)
	- optional `reason`
4. If deepeval cannot run (for example no judge credentials), and `QUALITY_CONTROL_FAIL_OPEN=1`, the app returns a deterministic lexical-overlap fallback score instead of failing the request.

Minimal enablement:

```bash
QUALITY_CONTROL_ENABLED=1
QUALITY_CONTROL_THRESHOLD=0.5
```

If using an external judge model, provide provider credentials in `.env` (for example `OPENAI_API_KEY`) so deepeval can call the judge model.

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

Constraints:

- Only PDF files are supported.
- Maximum upload size is 50 MB.

### `DELETE /api/documents/{document_id}`

Deletes a document from local storage and the vector store.

### `POST /api/chat`

Accepts a JSON body like:

```json
{
	"question": "Where are uploaded documents stored?",
	"session_id": "demo-user-1"
}
```

Returns a grounded answer and citation list with filenames only.

When quality control is enabled, the response also includes:

```json
"quality_control": {
	"score": 0.84,
	"passed": true,
	"method": "deepeval.answer_relevancy",
	"reason": "The answer directly addresses the user question."
}
```

`session_id` is optional and defaults to `default`. Provide a stable `session_id` per user/client to enable multi-turn memory.

Guardrails:

- Requests that attempt to override hidden/system instructions are rejected.
- Requests for explicit sexual/nudity content are rejected.

### Optional: run Redis locally

```bash
docker run --name doctongue-redis -p 6379:6379 -d redis:7-alpine
```

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
