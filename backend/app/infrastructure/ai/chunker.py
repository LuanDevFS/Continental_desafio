from app.infrastructure.ai.text import split_sentences


class TextChunker:
    """Divide el texto en chunks respetando oraciones.

    El solape repite la última oración del chunk anterior para que una
    respuesta no quede cortada justo en el borde entre dos chunks.
    """

    def __init__(self, max_chars: int = 900, overlap_sentences: int = 1):
        if max_chars <= 0:
            raise ValueError("max_chars debe ser positivo")
        if overlap_sentences < 0:
            raise ValueError("overlap_sentences no puede ser negativo")
        self.max_chars = max_chars
        self.overlap_sentences = overlap_sentences

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
        current: list[str] = []
        current_len = 0
        for piece in pieces:
            if current and current_len + len(piece) + 1 > self.max_chars:
                chunks.append("\n".join(current))
                current = current[-self.overlap_sentences :] if self.overlap_sentences else []
                current_len = sum(len(p) + 1 for p in current)
            current.append(piece)
            current_len += len(piece) + 1
        if current:
            chunks.append("\n".join(current))
        return chunks
