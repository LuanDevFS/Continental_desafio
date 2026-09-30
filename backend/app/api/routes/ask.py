from fastapi import APIRouter, Depends

from app.api.deps import get_ask_question
from app.api.schemas import AskRequest, AskResponse, SourceOut
from app.application.ask_question import AskQuestion

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    use_case: AskQuestion = Depends(get_ask_question),
) -> AskResponse:
    result = await use_case.execute(
        session_id=body.session_id.strip(),
        question=body.question.strip(),
    )
    return AskResponse(
        session_id=body.session_id,
        answer=result.answer,
        sources=[SourceOut(document=s.document, snippet=s.snippet, score=s.score) for s in result.sources],
        created_at=result.created_at,
    )
