import math
from collections import Counter

from app.domain.models import Chunk, RetrievedChunk
from app.infrastructure.ai.text import tokenize


class TfidfIndex:
    """Índice TF-IDF en memoria sobre los chunks del documento.

    Elegí no meter una dependencia pesada (scikit-learn, faiss, etc.) para
    un volumen de texto chico: con unas pocas decenas de chunks alcanza y
    sobra, y el Dockerfile queda flaco. Si el corpus creciera, esto se
    cambia por embeddings + una base vectorial sin tocar el dominio
    (ver DECISION_LOG.md).
    """

    def __init__(self, chunks: list[Chunk]):
        self._chunks = chunks
        doc_tokens = [tokenize(c.text) for c in chunks]
        n = len(chunks)

        df: Counter[str] = Counter()
        for tokens in doc_tokens:
            df.update(set(tokens))

        # idf con suavizado estilo sklearn: log((1+n)/(1+df)) + 1
        self._idf = {term: math.log((1 + n) / (1 + freq)) + 1 for term, freq in df.items()}
        self._vectors = [self._vectorize(tokens) for tokens in doc_tokens]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        tf = Counter(tokens)
        vec = {t: (count / len(tokens)) * self._idf[t] for t, count in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values()))
        return {t: w / norm for t, w in vec.items()} if norm else {}

    def search(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        tokens = [t for t in tokenize(query) if t in self._idf]
        if not tokens:
            return []
        qvec = self._vectorize(tokens)

        scored = []
        for chunk, cvec in zip(self._chunks, self._vectors, strict=True):
            # las queries son cortas: conviene iterar sobre el vector más chico
            small, big = (qvec, cvec) if len(qvec) <= len(cvec) else (cvec, qvec)
            score = sum(w * big.get(t, 0.0) for t, w in small.items())
            if score > 0:
                scored.append(RetrievedChunk(chunk=chunk, score=score))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]
