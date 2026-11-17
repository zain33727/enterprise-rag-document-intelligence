from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import Conversation, Message, MessageRole, RetrievedSource
from app.schemas.conversation import AnswerResponse, AskRequest, Citation, ConversationResponse
from app.services.embeddings import get_embedding_provider
from app.services.llm import get_llm_provider
from app.services.rag import build_context
from app.services.retrieval import hybrid_search

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(session: AsyncSession = Depends(get_db)) -> Conversation:
    conversation = Conversation()
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@router.post("/{conversation_id}/messages", response_model=AnswerResponse)
async def ask_question(
    conversation_id: UUID,
    request: AskRequest,
    session: AsyncSession = Depends(get_db),
) -> AnswerResponse:
    conversation = await session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        embedding_provider = get_embedding_provider()
        chunks = await hybrid_search(
            session, request.question, embedding_provider, top_k=request.top_k
        )
        history_rows = (
            await session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(20)
            )
        ).all()
        history = [{"role": message.role.value, "content": message.content} for message in history_rows]
        llm = get_llm_provider()
        answer = await llm.answer(
            question=request.question,
            context=build_context(chunks),
            history=history,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    user_message = Message(
        conversation_id=conversation_id, role=MessageRole.user, content=request.question
    )
    assistant_message = Message(
        conversation_id=conversation_id, role=MessageRole.assistant, content=answer
    )
    session.add_all([user_message, assistant_message])
    await session.flush()
    citations = [
        Citation(
            source_number=index,
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            content=chunk.content,
            score=chunk.score,
            page_number=chunk.page_number,
            sheet_name=chunk.sheet_name,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    session.add_all(
        [
            RetrievedSource(
                message_id=assistant_message.id,
                chunk_id=citation.chunk_id,
                rank=citation.source_number,
                score=citation.score,
            )
            for citation in citations
        ]
    )
    await session.commit()
    return AnswerResponse(
        conversation_id=conversation_id,
        message_id=assistant_message.id,
        answer=answer,
        citations=citations,
    )
