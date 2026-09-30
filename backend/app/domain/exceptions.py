class AppError(Exception):
    """Base para los errores de negocio de la aplicación."""


class UnsupportedFileTypeError(AppError):
    def __init__(self, filename: str, supported: list[str]):
        super().__init__(f"Tipo de archivo no soportado: {filename}. Formatos válidos: {', '.join(supported)}")
        self.filename = filename


class EmptyDocumentError(AppError):
    def __init__(self, filename: str):
        super().__init__(f"El documento '{filename}' no contiene texto extraíble.")
        self.filename = filename


class DocumentTooLargeError(AppError):
    def __init__(self, filename: str, max_bytes: int):
        super().__init__(f"El documento '{filename}' supera el tamaño máximo de {max_bytes // (1024 * 1024)} MB.")
        self.filename = filename


class NoDocumentLoadedError(AppError):
    def __init__(self):
        super().__init__("No hay ningún documento cargado. Sube un documento antes de preguntar.")


class AssistantUnavailableError(AppError):
    """El proveedor de IA externo falló o no está disponible."""
