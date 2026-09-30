from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AskRequest(BaseModel):
    session_id: NonEmptyStr = Field(max_length=128)
    question: NonEmptyStr = Field(max_length=4000)


class SourceOut(BaseModel):
    document: str
    snippet: str
    score: float


class AskResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceOut]
    created_at: datetime


class DocumentOut(BaseModel):
    id: str
    filename: str
    size_bytes: int
    chunk_count: int
    uploaded_at: datetime


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceOut]
    created_at: datetime


class HistoryOut(BaseModel):
    session_id: str
    messages: list[MessageOut]


class HealthOut(BaseModel):
    status: str
    assistant: str
