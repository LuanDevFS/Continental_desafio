import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.exceptions import NoDocumentLoadedError
from app.domain.models import NO_ANSWER, Chunk, Message, Source
from app.domain.ports import (
    AssistantEngine,
    DocumentRepository,
    MessageRepository,
    Retriever,
)


@dataclass
class AskResult:
    answer: str
    sources: list[Source]
    created_at: datetime


class AskQuestion:
    """Recupera los chunks relevantes, le pasa el contexto al asistente
    y persiste el intercambio en el historial de la sesión."""

    def __init__(
        self,
        documents: DocumentRepository,
        messages: MessageRepository,
        retriever_factory: Callable[[list[Chunk]], Retriever],
        assistant: AssistantEngine,
        top_k: int,
        min_score: float,
    ):
        self._documents = documents
        self._messages = messages
        self._retriever_factory = retriever_factory
        self._assistant = assistant
        self._top_k = top_k
        self._min_score = min_score

    async def execute(self, session_id: str, question: str) -> AskResult:
        chunks = await self._documents.all_chunks()
        if not chunks:
            raise NoDocumentLoadedError()

        # TODO: si el corpus crece mucho, cachear el índice e invalidarlo
        # cuando se sube un documento nuevo (hoy tarda <1ms, no vale la pena)
        retriever = self._retriever_factory(chunks)
        hits = retriever.search(question, k=self._top_k)
        relevant = [h for h in hits if h.score >= self._min_score]

        if relevant:
            answer = await self._assistant.answer(question, relevant)
            sources = [
                Source(
                    document=hit.chunk.document_name,
                    snippet=_snippet(hit.chunk.text),
                    score=hit.score,
                )
                for hit in relevant
            ]
        else:
            answer = NO_ANSWER
            sources = []

        now = datetime.now(UTC)
        await self._messages.append(
            Message(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="user",
                content=question,
                created_at=now,
            )
        )
        await self._messages.append(
            Message(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="assistant",
                content=answer,
                created_at=datetime.now(UTC),
                sources=[s.to_dict() for s in sources],
            )
        )
        return AskResult(answer=answer, sources=sources, created_at=now)


def _snippet(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"
