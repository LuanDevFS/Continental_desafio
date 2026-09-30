from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

NO_ANSWER = (
    "No encontré información suficiente en el documento para responder esa "
    "pregunta. Prueba reformularla o verifica que el documento cargado cubra "
    "el tema."
)


@dataclass
class Document:
    id: str
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    uploaded_at: datetime


@dataclass
class Chunk:
    id: str
    document_id: str
    position: int
    text: str
    document_name: str = ""


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass
class Source:
    document: str
    snippet: str
    score: float

    def to_dict(self) -> dict:
        return {
            "document": self.document,
            "snippet": self.snippet,
            "score": round(self.score, 4),
        }


@dataclass
class Message:
    id: str
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
    sources: list[dict] = field(default_factory=list)
