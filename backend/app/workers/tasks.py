import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete

from app.db.session import session_factory
from app.models.document import (
    Document,
    DocumentChunk,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
)
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_provider
from app.services.extraction import extract_content
from app.workers.celery_app import celery_app


async def _process_document(document_id: UUID, job_id: UUID) -> None:
    async with session_factory() as session:
        job = await session.get(IngestionJob, job_id)
        document = await session.get(Document, document_id)
        if not job or not document:
            return
        job.status = IngestionJobStatus.processing
        job.attempts += 1
        job.started_at = datetime.now(UTC)
        document.status = DocumentStatus.extracting
        await session.commit()
        try:
            data = await asyncio.to_thread(Path(document.storage_path).read_bytes)
            extracted = extract_content(document.original_filename, data)
            document.extracted_text = extracted.text
            document.status = DocumentStatus.chunking
            await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
            chunks = chunk_text(extracted.text)
            document.status = DocumentStatus.embedding
            embeddings = get_embedding_provider().embed_documents([chunk.content for chunk in chunks])
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                session.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        embedding=embedding,
                        start_offset=chunk.start_offset,
                        end_offset=chunk.end_offset,
                    )
                )
            document.status = DocumentStatus.indexed
            job.status = IngestionJobStatus.completed
            job.completed_at = datetime.now(UTC)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            document = await session.get(Document, document_id)
            job = await session.get(IngestionJob, job_id)
            if document:
                document.status = DocumentStatus.failed
                document.error_message = str(exc)[:2000]
            if job:
                job.status = IngestionJobStatus.failed
                job.error_message = str(exc)[:2000]
                job.completed_at = datetime.now(UTC)
            await session.commit()
            raise


@celery_app.task(
    bind=True,
    autoretry_for=(RuntimeError, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document_task(self, document_id: str, job_id: str) -> None:
    asyncio.run(_process_document(UUID(document_id), UUID(job_id)))
