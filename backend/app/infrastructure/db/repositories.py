import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Chunk, Document, Message
from app.infrastructure.db.tables import ChunkRow, DocumentRow, MessageRow


class SqlDocumentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, document: Document, chunks: list[Chunk]) -> None:
        self._session.add(
            DocumentRow(
                id=document.id,
                filename=document.filename,
                content_type=document.content_type,
                size_bytes=document.size_bytes,
                chunk_count=document.chunk_count,
                text="\n".join(c.text for c in chunks),
                uploaded_at=document.uploaded_at,
            )
        )
        self._session.add_all(
            ChunkRow(
                id=c.id,
                document_id=c.document_id,
                position=c.position,
                text=c.text,
            )
            for c in chunks
        )
        await self._session.commit()

    async def list_documents(self) -> list[Document]:
        rows = await self._session.scalars(
            select(DocumentRow).order_by(DocumentRow.uploaded_at.desc())
        )
        return [
            Document(
                id=row.id,
                filename=row.filename,
                content_type=row.content_type,
                size_bytes=row.size_bytes,
                chunk_count=row.chunk_count,
                uploaded_at=row.uploaded_at,
            )
            for row in rows
        ]

    async def all_chunks(self) -> list[Chunk]:
        rows = await self._session.execute(
            select(ChunkRow, DocumentRow.filename)
            .join(DocumentRow, ChunkRow.document_id == DocumentRow.id)
            .order_by(ChunkRow.document_id, ChunkRow.position)
        )
        return [
            Chunk(
                id=row.id,
                document_id=row.document_id,
                position=row.position,
                text=row.text,
                document_name=filename,
            )
            for row, filename in rows
        ]


class SqlMessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, message: Message) -> None:
        self._session.add(
            MessageRow(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                sources_json=json.dumps(message.sources, ensure_ascii=False),
                created_at=message.created_at,
            )
        )
        await self._session.commit()

    async def list_by_session(self, session_id: str) -> list[Message]:
        rows = await self._session.scalars(
            select(MessageRow).where(MessageRow.session_id == session_id).order_by(MessageRow.created_at)
        )
        return [
            Message(
                id=row.id,
                session_id=row.session_id,
                role=row.role,
                content=row.content,
                created_at=row.created_at,
                sources=json.loads(row.sources_json or "[]"),
            )
            for row in rows
        ]
