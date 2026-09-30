from app.domain.models import Document, Message
from app.domain.ports import DocumentRepository, MessageRepository


class GetHistory:
    def __init__(self, messages: MessageRepository):
        self._messages = messages

    async def execute(self, session_id: str) -> list[Message]:
        return await self._messages.list_by_session(session_id)


class ListDocuments:
    def __init__(self, documents: DocumentRepository):
        self._documents = documents

    async def execute(self) -> list[Document]:
        return await self._documents.list_documents()
