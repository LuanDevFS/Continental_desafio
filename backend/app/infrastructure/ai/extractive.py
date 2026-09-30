from collections import Counter

from app.domain.models import NO_ANSWER, RetrievedChunk
from app.infrastructure.ai.text import split_sentences, tokenize


def _sentence_score(question_tokens: Counter, sentence: str) -> float:
    tokens = tokenize(sentence)
    if not tokens or not question_tokens:
        return 0.0
    overlap = sum((question_tokens & Counter(tokens)).values())
    # F1 simple entre tokens de la pregunta y de la oración
    precision = overlap / sum(Counter(tokens).values())
    recall = overlap / sum(question_tokens.values())
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


class ExtractiveAssistant:
    """Asistente local: compone la respuesta citando las oraciones del
    documento más relacionadas con la pregunta.

    Es el modo por defecto cuando no hay un LLM configurado. Al responder
    solo con texto literal del documento, no puede inventar datos.
    """

    def __init__(self, max_sentences: int = 3, min_sentence_score: float = 0.05):
        self.max_sentences = max_sentences
        self.min_sentence_score = min_sentence_score

    async def answer(self, question: str, context: list[RetrievedChunk]) -> str:
        q_tokens = Counter(tokenize(question))

        candidates: list[tuple[float, int, str]] = []
        for position, hit in enumerate(context):
            for sentence in split_sentences(hit.chunk.text):
                score = _sentence_score(q_tokens, sentence)
                if score >= self.min_sentence_score:
                    candidates.append((score, position, sentence))

        if not candidates:
            return NO_ANSWER

        # mejores oraciones primero; desempata el orden en el documento
        candidates.sort(key=lambda c: (-c[0], c[1]))
        chosen = candidates[: self.max_sentences]

        # las devolvemos en el orden en que aparecen en el contexto
        chosen.sort(key=lambda c: c[1])
        return " ".join(sentence for _, _, sentence in chosen)
