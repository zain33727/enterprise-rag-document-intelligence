import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document, DocumentStatus, IngestionJob
from app.services.extraction import MEDIA_TYPES
from app.workers.tasks import process_document_task


async def ingest_upload(session: AsyncSession, upload: UploadFile) -> Document:
    settings = get_settings()
    filename = Path(upload.filename or "").name
    suffix = Path(filename).suffix.lower()
    if not filename or suffix not in MEDIA_TYPES:
        raise ValueError("Supported file types are PDF, DOCX, XLSX, CSV, and TXT")
    if upload.content_type and upload.content_type != MEDIA_TYPES[suffix]:
        raise ValueError("Uploaded content type does not match the file extension")

    data = await upload.read(settings.max_upload_size_bytes + 1)
    if len(data) > settings.max_upload_size_bytes:
        raise ValueError(f"File exceeds the {settings.max_upload_size_bytes} byte limit")
    content_hash = hashlib.sha256(data).hexdigest()
    existing = await session.scalar(select(Document).where(Document.content_hash == content_hash))
    if existing:
        raise FileExistsError(f"Document already exists with id {existing.id}")

    document_id = uuid.uuid4()
    stored_filename = f"{document_id}{suffix}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = upload_dir / stored_filename
    storage_path.write_bytes(data)
    document = Document(
        id=document_id,
        original_filename=filename,
        stored_filename=stored_filename,
        storage_path=str(storage_path),
        content_hash=content_hash,
        media_type=MEDIA_TYPES[suffix],
        size_bytes=len(data),
        status=DocumentStatus.queued,
    )
    job = IngestionJob(document_id=document_id)
    session.add(document)
    session.add(job)
    await session.commit()
    await session.refresh(document)
    process_document_task.delay(str(document.id), str(job.id))
    return document
