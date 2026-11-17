# API reference

The interactive OpenAPI reference is available at `/docs` when the backend is
running.

## Health

- `GET /api/v1/health`

## Documents

- `POST /api/v1/documents` — upload one PDF, DOCX, XLSX, CSV, or TXT file
- `GET /api/v1/documents` — paginated listing with optional filename search
- `GET /api/v1/documents/{id}` — retrieve document metadata
- `DELETE /api/v1/documents/{id}` — delete the file, document, and chunks
- `POST /api/v1/documents/{id}/reindex` — queue reprocessing

## Retrieval and conversations

- `POST /api/v1/search` — hybrid keyword/vector chunk search
- `POST /api/v1/conversations` — create a conversation
- `POST /api/v1/conversations/{id}/messages` — ask a grounded question

## Monitoring

- `GET /api/v1/ingestion/jobs` — list asynchronous ingestion jobs
