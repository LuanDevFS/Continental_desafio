import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    AppError,
    AssistantUnavailableError,
    DocumentTooLargeError,
    EmptyDocumentError,
    NoDocumentLoadedError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR = {
    UnsupportedFileTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    DocumentTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
    EmptyDocumentError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    NoDocumentLoadedError: status.HTTP_409_CONFLICT,
    AssistantUnavailableError: status.HTTP_502_BAD_GATEWAY,
}


def _make_handler(http_status: int):
    async def handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=http_status, content={"detail": str(exc)})

    return handler


def register_error_handlers(app: FastAPI) -> None:
    for exc_type, http_status in _STATUS_BY_ERROR.items():
        app.add_exception_handler(exc_type, _make_handler(http_status))

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor."},
        )
