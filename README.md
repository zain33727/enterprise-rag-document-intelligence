# Enterprise RAG Document Intelligence

An enterprise-oriented Retrieval-Augmented Generation platform for uploading,
processing, indexing, searching, and querying organizational documents.

## Current status

The repository currently contains the Phase 1 foundation:

- FastAPI backend with `/api/v1/health`
- Pydantic settings loaded from environment variables
- SQLAlchemy async database session and initial `documents` model
- Alembic migration for the documents table
- Document upload, duplicate detection, extraction, chunking, and deletion APIs
- PDF, DOCX, XLSX, CSV, and TXT extraction support
- Configurable sentence-transformer embeddings with pgvector storage
- PostgreSQL full-text plus vector hybrid search at `/api/v1/search`
- Grounded conversation APIs with Groq answers and persisted source citations
- Redis/Celery queued ingestion with retryable jobs and monitoring APIs
- React dashboard with document management, assistant, overview, and ingestion monitor views
- Security headers, upload content-type validation, focused extraction tests, and a 1,000-document benchmark generator
- PostgreSQL/pgvector and Redis Docker services
- React, TypeScript, and Vite frontend shell
- Backend health test and frontend production build

Retrieval, asynchronous processing, and the full dashboard are being added
incrementally.

## Technology

- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
- React 19, TypeScript, Vite
- PostgreSQL with pgvector
- Redis and Celery (planned in the ingestion phase)
- Configurable LLM and embedding providers

## Local development

### Backend

```bash
cp .env.example .env
python -m pip install -e 'backend[dev]'
PYTHONPATH=backend uvicorn app.main:app --reload
```

Install local sentence-transformer embeddings and Groq support when indexing
documents and generating answers:

```bash
python -m pip install -e 'backend[ai]'
```

The API is available at http://localhost:8000 and interactive documentation is
available at http://localhost:8000/docs.

Run backend checks:

```bash
PYTHONPATH=backend python -m pytest -q
python -m ruff check backend
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at http://localhost:5173.

### Infrastructure

Start PostgreSQL, Redis, and the worker infrastructure:

```bash
docker compose up -d postgres redis
```

Run the API and worker containers together with `docker compose up --build`.

Apply database migrations after the database is running:

```bash
cd backend
alembic upgrade head
```

The full backend container can be started with `docker compose up --build`.

## Architecture and API reference

- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- Generate a local benchmark corpus with:

  ```bash
  python scripts/benchmark_ingestion.py --count 1000
  ```

  The generated files are explicitly synthetic and are not production
  performance results.

  ## Known limitations

  - Authentication, tenant authorization, and object storage adapters are not yet
    enabled; the current deployment is a local development foundation.
  - The assistant response is request/response rather than token streaming.
  - Local embedding models and Groq credentials must be installed/configured
    separately.

## Planned implementation phases

1. Backend foundation and database migrations
2. Upload, extraction, normalization, chunking, and document APIs
3. Embeddings, pgvector indexing, and hybrid retrieval
4. Grounded RAG answers, citations, and conversations
5. Redis/Celery ingestion workers and monitoring
6. Document-management dashboard
7. Assistant, analytics, and settings interfaces
8. Security hardening, benchmarks, deployment documentation, and end-to-end tests

API keys belong only in `.env`; never commit them.
