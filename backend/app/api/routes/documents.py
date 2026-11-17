from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import Document, DocumentStatus, IngestionJob
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.documents import ingest_upload
from app.workers.tasks import process_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...), session: AsyncSession = Depends(get_db)
) -> Document:
    try:
        return await ingest_upload(session, file)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    query = select(Document)
    count_query = select(func.count()).select_from(Document)
    if search:
        pattern = f"%{search}%"
        query = query.where(Document.original_filename.ilike(pattern))
        count_query = count_query.where(Document.original_filename.ilike(pattern))
    total = await session.scalar(count_query) or 0
    items = (
        await session.scalars(
            query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).all()
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, session: AsyncSession = Depends(get_db)) -> Document:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, session: AsyncSession = Depends(get_db)) -> None:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    Path(document.storage_path).unlink(missing_ok=True)
    await session.delete(document)
    await session.commit()


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document(document_id: UUID, session: AsyncSession = Depends(get_db)) -> Document:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.status = DocumentStatus.queued
    document.error_message = None
    job = IngestionJob(document_id=document.id)
    session.add(job)
    await session.commit()
    await session.refresh(document)
    process_document_task.delay(str(document.id), str(job.id))
    return document
