from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.embeddings import get_embedding_provider
from app.services.retrieval import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest, session: AsyncSession = Depends(get_db)
) -> SearchResponse:
    try:
        provider = get_embedding_provider()
        results = await hybrid_search(session, request.query, provider, top_k=request.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return SearchResponse(
        query=request.query,
        results=[SearchResult.model_validate(result) for result in results],
    )
