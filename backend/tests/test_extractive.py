from app.domain.models import NO_ANSWER, Chunk, RetrievedChunk
from app.infrastructure.ai.extractive import ExtractiveAssistant


def hit(text: str, score: float = 0.5) -> RetrievedChunk:
    chunk = Chunk(id="1", document_id="d", position=0, text=text)
    return RetrievedChunk(chunk=chunk, score=score)


async def test_answer_uses_sentences_from_context():
    assistant = ExtractiveAssistant()
    context = [hit("El bono se paga en diciembre. Las vacaciones son de 15 días hábiles por año.")]
    answer = await assistant.answer("¿cuántos días de vacaciones?", context)
    assert "15 días" in answer
    assert "bono" not in answer


async def test_no_matching_sentences_returns_no_answer():
    assistant = ExtractiveAssistant(min_sentence_score=0.9)
    context = [hit("Texto completamente ajeno al tema consultado.")]
    answer = await assistant.answer("¿cuántos días de vacaciones?", context)
    assert answer == NO_ANSWER
