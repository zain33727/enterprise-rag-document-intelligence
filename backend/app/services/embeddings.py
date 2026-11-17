from collections.abc import Sequence
from typing import Protocol

from app.core.config import get_settings


class EmbeddingProvider(Protocol):
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class SentenceTransformerProvider:
    def __init__(self, model_name: str, dimension: int) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Local embeddings require the optional AI dependencies. "
                "Install with: pip install -e 'backend[ai]'"
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.dimension = dimension

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._model.encode(list(texts), normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], normalize_embeddings=True)[0].tolist()


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider != "local":
        raise RuntimeError(f"Unsupported embedding provider: {settings.embedding_provider}")
    return SentenceTransformerProvider(settings.embedding_model, settings.embedding_dimension)
