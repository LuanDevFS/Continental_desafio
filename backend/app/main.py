import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.routes import ask, documents, history
from app.api.schemas import HealthOut
from app.config import Settings, get_settings
from app.domain.ports import AssistantEngine
from app.infrastructure.ai.extractive import ExtractiveAssistant
from app.infrastructure.ai.openai_assistant import OpenAIAssistant
from app.infrastructure.db.engine import build_engine, build_session_factory
from app.infrastructure.db.tables import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_assistant(settings: Settings) -> AssistantEngine:
    if settings.openai_api_key:
        logger.info("Asistente: OpenAI (modelo %s)", settings.llm_model)
        return OpenAIAssistant(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.openai_base_url,
        )
    logger.info("Asistente: extractivo local (sin API key configurada)")
    return ExtractiveAssistant()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    async with engine.begin() as conn:
        # create_all alcanza para el alcance del desafío; con más tablas
        # iría Alembic
        await conn.run_sync(Base.metadata.create_all)

    app.state.session_factory = build_session_factory(engine)
    app.state.assistant = build_assistant(settings)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="doc-qa", lifespan=lifespan)

    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    @app.get("/health", response_model=HealthOut)
    async def health() -> HealthOut:
        assistant = app.state.assistant
        return HealthOut(
            status="ok",
            assistant=type(assistant).__name__,
        )

    app.include_router(documents.router, tags=["documents"])
    app.include_router(ask.router, tags=["ask"])
    app.include_router(history.router, tags=["history"])

    frontend_dir = Path(settings.frontend_dir)
    if frontend_dir.is_dir():
        # el SPA se sirve desde el mismo proceso; va último para no
        # pisar las rutas de la API
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    else:
        logger.warning("Frontend no encontrado en %s", frontend_dir)

    return app


app = create_app()
