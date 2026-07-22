# DocTongue

DocTongue is a simple full-stack document Q&A application. Users upload PDFs into a shared collection, ask questions in a chat-style interface, and receive answers grounded only in retrieved document content with visible supporting evidence.

![DocTongue app screenshot](Screenshot%202026-07-21%20175709.png)

## Features

- The system indexes uploaded PDFs and makes them searchable across the shared document collection.
- The system provides chat-based question answering grounded in indexed document evidence.
- The system returns citation references for factual answers, showing source filenames.
- The system maintains short multi-turn conversation context per chat session.
- The system records each completed chat exchange (timestamp, user question, assistant answer) in an audit log.
- The system rejects prompt-injection attempts that request hidden instructions or policy bypass.
- The system rejects explicit sexual or nudity-related requests.
- The system allows users to view indexed documents and delete documents from the collection.
- The system provides an optional response quality control with deepeval (LLM-as-judge) and a safe lexical fallback


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

Copy `.env.example` to `backend/.env` and adjust values as needed.

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

Functional requirements:

1. The system stores recent chat turns per `session_id` and uses that context to improve follow-up question handling.
2. The system limits retained context to `CHAT_MEMORY_WINDOW` recent turns.
3. The system continues to answer the current user question while using session context to improve retrieval relevance.
4. The system appends each completed turn back into session memory.
5. The system continues operating when Redis is unavailable by using a local fallback memory mechanism.
6. The system writes chat audit entries to `backend/data/chat_audit.txt` by default, unless `CHAT_AUDIT_LOG_PATH` is provided.

### Quality control (deepeval)

Functional requirements:

1. The system supports optional response quality evaluation when `QUALITY_CONTROL_ENABLED=1`.
2. The system returns a `quality_control` object for evaluated responses containing `score`, `passed`, and `method` fields.
3. The system computes `passed` using `QUALITY_CONTROL_THRESHOLD`.
4. The system includes `reason` when `QUALITY_CONTROL_INCLUDE_REASON=1`.
5. The system keeps chat responses available when judge evaluation fails if `QUALITY_CONTROL_FAIL_OPEN=1`.
6. The system returns judge-based evaluation metadata when judge execution succeeds.

Minimal enablement:

```bash
QUALITY_CONTROL_ENABLED=1
QUALITY_CONTROL_THRESHOLD=0.5
```

If using an external judge model, provide provider credentials in `.env` (for example `OPENAI_API_KEY`) so deepeval can call the judge model.

## Docker setup (recommended)

The repository includes Dockerfiles for both apps and a root `docker-compose.yml` that starts:

- `frontend` on `http://localhost:3000`
- `backend` on `http://localhost:8000`

By default, the backend uses its in-process chat memory fallback so the Compose stack does not require a separate Redis container.

From the repository root:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

Stop services and remove Redis volume data:

```bash
docker compose down -v
```

Notes:

- Backend document/chroma/audit storage is persisted from `./backend/data` to `/app/data` in the backend container.
- `frontend` uses `BACKEND_API_BASE_URL=http://backend:8000` inside Compose so `/api/*` requests resolve to the backend service.
- The frontend rewrite target is compiled during image build. If you change `BACKEND_API_BASE_URL`, rebuild the frontend image (`docker compose up --build`).
- Provider credentials such as `OPENAI_API_KEY`, `LLM_API_KEY`, and `EMBEDDING_API_KEY` can be exported in your shell (or set in a local `.env`) before running Compose.
- If you want Redis-backed chat memory, run a Redis container separately and set `REDIS_URL` accordingly.

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
