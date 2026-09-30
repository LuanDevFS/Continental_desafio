import uuid
from datetime import UTC, datetime

from app.domain.exceptions import DocumentTooLargeError
from app.domain.models import Chunk, Document
from app.domain.ports import DocumentRepository
from app.infrastructure.ai.chunker import TextChunker
from app.infrastructure.documents.loader import extract_text


class RegisterDocument:
    def __init__(
        self,
        documents: DocumentRepository,
        chunker: TextChunker,
        max_bytes: int,
    ):
        self._documents = documents
        self._chunker = chunker
        self._max_bytes = max_bytes

    async def execute(self, filename: str, content_type: str, data: bytes) -> Document:
        if len(data) > self._max_bytes:
            raise DocumentTooLargeError(filename, self._max_bytes)

        text = extract_text(filename, data)
        chunks = self._chunker.split(text)

        document = Document(
            id=uuid.uuid4().hex,
            filename=filename,
            content_type=content_type or "",
            size_bytes=len(data),
            chunk_count=len(chunks),
            uploaded_at=datetime.now(UTC),
        )
        chunk_entities = [
            Chunk(
                id=uuid.uuid4().hex,
                document_id=document.id,
                position=i,
                text=chunk_text,
                document_name=filename,
            )
            for i, chunk_text in enumerate(chunks)
        ]
        await self._documents.save(document, chunk_entities)
        return document
