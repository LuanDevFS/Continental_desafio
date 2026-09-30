from app.infrastructure.ai.text import split_sentences


class TextChunker:
    """Divide el texto en chunks solapados respetando oraciones.

    El solape evita que una respuesta quede cortada justo en el borde
    entre dos chunks.
    """

    def __init__(self, max_chars: int = 900, overlap_chars: int = 150):
        if max_chars <= 0:
            raise ValueError("max_chars debe ser positivo")
        if overlap_chars >= max_chars:
            raise ValueError("overlap_chars debe ser menor que max_chars")
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def split(self, text: str) -> list[str]:
        pieces: list[str] = []
        for sentence in split_sentences(text):
            if len(sentence) <= self.max_chars:
                pieces.append(sentence)
            else:
                # oración gigante (o texto sin puntuación): corte a lo bruto
                for i in range(0, len(sentence), self.max_chars):
                    pieces.append(sentence[i : i + self.max_chars])

        chunks: list[str] = []
        current = ""
        for piece in pieces:
            candidate = f"{current} {piece}" if current else piece
            if len(candidate) > self.max_chars and current:
                chunks.append(current)
                tail = current[-self.overlap_chars :] if self.overlap_chars else ""
                current = f"{tail} {piece}".strip()
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks
