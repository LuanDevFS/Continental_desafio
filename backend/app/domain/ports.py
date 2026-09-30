from __future__ import annotations

from typing import Protocol

from app.domain.models import Chunk, Document, Message, RetrievedChunk


class DocumentRepository(Protocol):
    async def save(self, document: Document, chunks: list[Chunk]) -> None: ...

    async def list_documents(self) -> list[Document]: ...

    async def all_chunks(self) -> list[Chunk]: ...


class MessageRepository(Protocol):
    async def append(self, message: Message) -> None: ...

    async def list_by_session(self, session_id: str) -> list[Message]: ...


class Retriever(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


class AssistantEngine(Protocol):
    async def answer(self, question: str, context: list[RetrievedChunk]) -> str: ...
