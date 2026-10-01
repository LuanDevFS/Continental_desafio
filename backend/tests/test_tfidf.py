from app.domain.models import Chunk
from app.infrastructure.ai.tfidf import TfidfIndex


def make_chunks(texts: list[str]) -> list[Chunk]:
    return [Chunk(id=str(i), document_id="doc1", position=i, text=t) for i, t in enumerate(texts)]


def test_relevant_chunk_ranks_first():
    chunks = make_chunks(
        [
            "Las vacaciones son de 15 días hábiles por año calendario.",
            "El bono anual se paga en diciembre según performance.",
            "Se puede trabajar remoto 3 días por semana.",
        ]
    )
    hits = TfidfIndex(chunks).search("¿cuántos días de vacaciones tengo?", k=2)

    assert hits
    assert "vacaciones" in hits[0].chunk.text


def test_unrelated_query_returns_low_or_no_results():
    chunks = make_chunks(["Las vacaciones son de 15 días hábiles."])
    hits = TfidfIndex(chunks).search("¿cómo hacer un soufflé de chocolate?", k=3)
    assert hits == []


def test_accents_and_stopwords_are_normalized():
    chunks = make_chunks(["La informacion esta en el portal."])
    hits = TfidfIndex(chunks).search("¿dónde está la información?", k=1)
    assert hits and hits[0].score > 0


def test_empty_index_returns_nothing():
    assert TfidfIndex([]).search("algo", k=3) == []
