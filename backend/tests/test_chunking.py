import pytest

from app.services.chunking import chunk_text


def test_chunking_preserves_order_and_overlap() -> None:
    chunks = chunk_text("one two three four five six", chunk_size=13, overlap=4)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0].content == "one two"
    assert chunks[1].content.startswith("two")


def test_chunking_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=10, overlap=10)
