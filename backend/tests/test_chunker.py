from app.infrastructure.ai.chunker import TextChunker


def test_short_text_produces_single_chunk():
    chunker = TextChunker(max_chars=900)
    chunks = chunker.split("Un texto corto. Dos oraciones nomás.")
    assert len(chunks) == 1
    assert "Un texto corto" in chunks[0]
    assert "Dos oraciones" in chunks[0]


def test_long_text_splits_respecting_max_chars():
    chunker = TextChunker(max_chars=100, overlap_sentences=1)
    text = " ".join(f"Oración número {i} del documento." for i in range(30))
    chunks = chunker.split(text)

    assert len(chunks) > 1
    for chunk in chunks:
        # colchón por la oración solapada
        assert len(chunk) <= 100 + 40


def test_empty_text_returns_no_chunks():
    assert TextChunker().split("") == []
    assert TextChunker().split("   \n  ") == []


def test_invalid_params_raise():
    import pytest

    with pytest.raises(ValueError):
        TextChunker(max_chars=0)
    with pytest.raises(ValueError):
        TextChunker(overlap_sentences=-1)
