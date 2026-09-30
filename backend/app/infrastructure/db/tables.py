from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    filename: Mapped[str]
    content_type: Mapped[str] = mapped_column(default="")
    size_bytes: Mapped[int]
    chunk_count: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime]


class ChunkRow(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    position: Mapped[int]
    text: Mapped[str] = mapped_column(Text)


class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[str]
    role: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime]


Index("ix_messages_session_created", MessageRow.session_id, MessageRow.created_at)
