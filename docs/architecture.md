# Architecture

## Request and ingestion flow

1. The React client uploads a supported file to FastAPI.
2. FastAPI validates the extension, content type, size, and SHA-256 hash.
3. The file is stored through the configured local storage path.
4. A document and queued ingestion job are committed to PostgreSQL.
5. Celery publishes processing work through Redis.
6. The worker extracts text, normalizes it, chunks it, creates embeddings, and stores chunks.
7. Each chunk retains its document relationship and source offsets.

## Retrieval and answer flow

1. A query is embedded using the configured embedding provider.
2. PostgreSQL performs vector similarity and full-text keyword retrieval.
3. Reciprocal-rank fusion combines both result sets.
4. Only the top matching chunks are inserted into the LLM context.
5. The LLM is instructed to answer only from that context and cite numbered sources.
6. Messages and retrieved source relationships are persisted for auditability.

## Services

```text
React/Vite ──HTTP──> FastAPI ──> PostgreSQL + pgvector
                         │              │
                         └──> Redis <── Celery worker
```

The LLM and embedding providers are isolated behind service interfaces. API
keys are server-side settings and are never sent to the frontend.

## Data model

- `documents`: uploaded file metadata, lifecycle state, hash, and extracted text
- `document_chunks`: normalized retrieval units and embeddings
- `ingestion_jobs`: asynchronous processing state, attempts, and errors
- `conversations` / `messages`: user questions and grounded answers
- `retrieved_sources`: exact chunks used for each answer

The migrations in `backend/alembic/versions/` are the source of truth for the
database schema.
