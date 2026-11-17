from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 200) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        content = normalized[start:end].strip()
        if content:
            chunks.append(TextChunk(content, index, start, end))
            index += 1
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks
