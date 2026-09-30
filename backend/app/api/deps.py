from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ask_question import AskQuestion
from app.application.queries import GetHistory, ListDocuments
from app.application.register_document import RegisterDocument
from app.config import Settings, get_settings
from app.domain.ports import AssistantEngine
from app.infrastructure.ai.chunker import TextChunker
from app.infrastructure.ai.tfidf import TfidfIndex
from app.infrastructure.db.repositories import (
    SqlDocumentRepository,
    SqlMessageRepository,
)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_assistant(request: Request) -> AssistantEngine:
    return request.app.state.assistant


def get_register_document(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RegisterDocument:
    return RegisterDocument(
        documents=SqlDocumentRepository(session),
        chunker=TextChunker(),
        max_bytes=settings.max_upload_bytes,
    )


def get_ask_question(
    session: AsyncSession = Depends(get_session),
    assistant: AssistantEngine = Depends(get_assistant),
    settings: Settings = Depends(get_settings),
) -> AskQuestion:
    return AskQuestion(
        documents=SqlDocumentRepository(session),
        messages=SqlMessageRepository(session),
        retriever_factory=TfidfIndex,
        assistant=assistant,
        top_k=settings.retrieval_top_k,
        min_score=settings.min_similarity,
    )


def get_history(
    session: AsyncSession = Depends(get_session),
) -> GetHistory:
    return GetHistory(messages=SqlMessageRepository(session))


def get_list_documents(
    session: AsyncSession = Depends(get_session),
) -> ListDocuments:
    return ListDocuments(documents=SqlDocumentRepository(session))
