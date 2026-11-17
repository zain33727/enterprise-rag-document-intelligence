from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.services.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    score: float
    page_number: int | None
    sheet_name: str | None


async def hybrid_search(
    session: AsyncSession,
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int = 8,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []
    query_embedding = provider.embed_query(query)
    vector_rows = (
        await session.execute(
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k * 3)
        )
    ).all()
    keyword_rows = (
        await session.execute(
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                func.to_tsvector("english", DocumentChunk.content).op("@@")(
                    func.plainto_tsquery("english", query)
                )
            )
            .order_by(
                func.ts_rank_cd(
                    func.to_tsvector("english", DocumentChunk.content),
                    func.plainto_tsquery("english", query),
                ).desc()
            )
            .limit(top_k * 3)
        )
    ).all()

    scores: dict[UUID, float] = {}
    rows: dict[UUID, tuple[DocumentChunk, Document]] = {}
    for rank, (chunk, document) in enumerate(vector_rows):
        rows[chunk.id] = (chunk, document)
        scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (60 + rank + 1)
    for rank, (chunk, document) in enumerate(keyword_rows):
        rows[chunk.id] = (chunk, document)
        scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (60 + rank + 1)

    ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [
        RetrievedChunk(
            chunk_id=chunk_id,
            document_id=rows[chunk_id][1].id,
            filename=rows[chunk_id][1].original_filename,
            content=rows[chunk_id][0].content,
            score=scores[chunk_id],
            page_number=rows[chunk_id][0].page_number,
            sheet_name=rows[chunk_id][0].sheet_name,
        )
        for chunk_id in ranked
    ]
