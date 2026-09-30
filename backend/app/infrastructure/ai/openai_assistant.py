import logging

from openai import AsyncOpenAI, OpenAIError

from app.domain.exceptions import AssistantUnavailableError
from app.domain.models import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas usando ÚNICAMENTE la información "
    "del contexto provisto, que son fragmentos de un documento cargado por el "
    "usuario.\n"
    "Reglas:\n"
    "- Si el contexto no contiene la respuesta, dilo claramente: "
    '"El documento no contiene información suficiente para responder eso". '
    "No inventes datos ni uses conocimiento externo.\n"
    "- Responde en el mismo idioma de la pregunta, de forma concisa.\n"
    "- Si varios fragmentos se complementan, combínalos en una sola respuesta."
)


class OpenAIAssistant:
    """Asistente basado en la API de OpenAI (o cualquier endpoint compatible,
    p. ej. Ollama) usando los chunks recuperados como contexto."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def answer(self, question: str, context: list[RetrievedChunk]) -> str:
        context_text = "\n\n".join(
            f"[{i + 1}] ({hit.chunk.document_name}) {hit.chunk.text}" for i, hit in enumerate(context)
        )
        user_message = f"Contexto:\n{context_text}\n\nPregunta: {question}"

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
        except OpenAIError as exc:
            logger.exception("Error llamando al proveedor de IA")
            raise AssistantUnavailableError("El servicio de IA no está disponible en este momento.") from exc

        content = response.choices[0].message.content
        return content.strip() if content else ""
