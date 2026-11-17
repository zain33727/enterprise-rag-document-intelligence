from collections.abc import Sequence
from typing import Protocol

from app.core.config import get_settings


class LLMProvider(Protocol):
    async def answer(self, *, question: str, context: str, history: Sequence[dict[str, str]]) -> str:
        ...


class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        try:
            from groq import AsyncGroq
        except ImportError as exc:
            raise RuntimeError(
                "Groq support requires the optional AI dependencies. "
                "Install with: pip install -e 'backend[ai]'"
            ) from exc
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def answer(self, *, question: str, context: str, history: Sequence[dict[str, str]]) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a grounded enterprise document assistant. Answer only from the "
                    "provided context. Cite supporting sources using [1], [2], etc. If the "
                    "context does not support an answer, say that the documents do not provide "
                    "enough information. Never invent document names, page numbers, or citations."
                ),
            },
            *history,
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        response = await self._client.chat.completions.create(model=self._model, messages=messages)
        return response.choices[0].message.content or "The documents do not provide enough information."


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider != "groq":
        raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is required to generate grounded answers")
    return GroqProvider(settings.groq_api_key, settings.llm_model)
