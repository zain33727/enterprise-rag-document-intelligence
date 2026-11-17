from uuid import uuid4

from app.services.rag import build_context
from app.services.retrieval import RetrievedChunk


def test_context_contains_numbered_source_metadata() -> None:
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="policy.pdf",
        content="Retention is seven years.",
        score=0.5,
        page_number=4,
        sheet_name=None,
    )
    context = build_context([chunk])
    assert "[1] policy.pdf, page 4" in context
    assert "Retention is seven years." in context
