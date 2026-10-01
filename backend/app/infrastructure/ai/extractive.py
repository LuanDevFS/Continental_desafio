from collections import Counter

from app.domain.models import NO_ANSWER, RetrievedChunk
from app.infrastructure.ai.text import split_sentences, tokenize

# oraciones más cortas que esto suelen ser encabezados o fragmentos
_MIN_SENTENCE_TOKENS = 4


def _sentence_score(question_tokens: Counter, sentence_tokens: Counter) -> float:
    if not sentence_tokens or not question_tokens:
        return 0.0
    overlap = sum((question_tokens & sentence_tokens).values())
    # F1 simple entre tokens de la pregunta y de la oración
    precision = overlap / sum(sentence_tokens.values())
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

        candidates: list[tuple[float, int, int, str]] = []
        seen: set[str] = set()
        for chunk_pos, hit in enumerate(context):
            for sent_pos, sentence in enumerate(split_sentences(hit.chunk.text)):
                sent_tokens = Counter(tokenize(sentence))
                if sum(sent_tokens.values()) < _MIN_SENTENCE_TOKENS:
                    continue
                # el solape entre chunks puede repetir oraciones
                key = " ".join(sorted(sent_tokens))
                if key in seen:
                    continue
                seen.add(key)
                score = _sentence_score(q_tokens, sent_tokens)
                if score >= self.min_sentence_score:
                    candidates.append((score, chunk_pos, sent_pos, sentence))

        if not candidates:
            return NO_ANSWER

        best = max(c[0] for c in candidates)
        # descarta oraciones muy por debajo de la mejor: suelen compartir
        # alguna palabra suelta pero no responder la pregunta
        cutoff = max(self.min_sentence_score, best * 0.65)
        chosen = [c for c in candidates if c[0] >= cutoff]
        chosen.sort(key=lambda c: -c[0])
        chosen = chosen[: self.max_sentences]

        # las devolvemos en el orden en que aparecen en el documento
        chosen.sort(key=lambda c: (c[1], c[2]))
        return " ".join(sentence for _, _, _, sentence in chosen)
