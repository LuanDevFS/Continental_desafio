import io
import re

from pypdf import PdfReader

from app.domain.exceptions import EmptyDocumentError, UnsupportedFileTypeError

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

# un salto de línea simple en prosa suele ser wrapping del editor, no un
# párrafo nuevo; se preservan párrafos (\n\n) y líneas de lista/encabezado
_SOFT_BREAK = re.compile(r"(?<!\n)\n(?!\n)(?!\s*(?:[-*#•]|\d+[.)]))")


def extract_text(filename: str, data: bytes) -> str:
    """Extrae texto plano del archivo. Lanza AppError si no puede."""
    ext = _extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(filename, sorted(SUPPORTED_EXTENSIONS))

    text = _extract_pdf(data, filename) if ext == ".pdf" else data.decode("utf-8", errors="replace")
    text = _SOFT_BREAK.sub(" ", text).strip()
    if not text:
        raise EmptyDocumentError(filename)
    return text


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot >= 0 else ""


def _extract_pdf(data: bytes, filename: str) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise EmptyDocumentError(filename) from exc
