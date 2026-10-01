from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import get_delete_document, get_list_documents, get_register_document
from app.api.schemas import DocumentOut
from app.application.queries import DeleteDocument, ListDocuments
from app.application.register_document import RegisterDocument
from app.domain.models import Document

router = APIRouter()


@router.post(
    "/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    use_case: RegisterDocument = Depends(get_register_document),
) -> DocumentOut:
    document = await use_case.execute(
        filename=file.filename or "sin-nombre",
        content_type=file.content_type or "",
        data=await file.read(),
    )
    return _to_out(document)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    use_case: ListDocuments = Depends(get_list_documents),
) -> list[DocumentOut]:
    return [_to_out(d) for d in await use_case.execute()]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    use_case: DeleteDocument = Depends(get_delete_document),
) -> None:
    await use_case.execute(document_id)


def _to_out(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        filename=document.filename,
        size_bytes=document.size_bytes,
        chunk_count=document.chunk_count,
        uploaded_at=document.uploaded_at,
    )
