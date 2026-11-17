import pytest

from app.services.embeddings import SentenceTransformerProvider


def test_local_provider_reports_missing_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", None)
    with pytest.raises(RuntimeError, match="optional AI dependencies"):
        SentenceTransformerProvider("missing-model", 384)
