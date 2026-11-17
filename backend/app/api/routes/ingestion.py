from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import IngestionJob
from app.schemas.ingestion import IngestionJobListResponse

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/jobs", response_model=IngestionJobListResponse)
async def list_ingestion_jobs(
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> IngestionJobListResponse:
    total = await session.scalar(select(func.count()).select_from(IngestionJob)) or 0
    items = (
        await session.scalars(
            select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
        )
    ).all()
    return IngestionJobListResponse(items=items, total=total)
