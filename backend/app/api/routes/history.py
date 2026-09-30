from fastapi import APIRouter, Depends, Path

from app.api.deps import get_history
from app.api.schemas import HistoryOut, MessageOut, SourceOut
from app.application.queries import GetHistory

router = APIRouter()


@router.get("/history/{session_id}", response_model=HistoryOut)
async def get_session_history(
    session_id: str = Path(min_length=1, max_length=128),
    use_case: GetHistory = Depends(get_history),
) -> HistoryOut:
    messages = await use_case.execute(session_id)
    return HistoryOut(
        session_id=session_id,
        messages=[
            MessageOut(
                role=m.role,
                content=m.content,
                sources=[SourceOut(**s) for s in m.sources],
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
