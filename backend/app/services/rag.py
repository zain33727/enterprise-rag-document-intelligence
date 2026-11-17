from collections.abc import Sequence

from app.services.retrieval import RetrievedChunk


def build_context(chunks: Sequence[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{index}] {chunk.filename}"
        + (f", page {chunk.page_number}" if chunk.page_number else "")
        + (f", sheet {chunk.sheet_name}" if chunk.sheet_name else "")
        + f"\n{chunk.content}"
        for index, chunk in enumerate(chunks, start=1)
    )
