# doc-qa — asistente de preguntas sobre documentos

App web para hacerle preguntas a un documento: subes un `.txt`, `.md` o
`.pdf` y chateas contra su contenido. API REST en FastAPI + SPA en
HTML/CSS/JS servida por el mismo proceso. El historial queda guardado en
SQLite.

El asistente responde solo con lo que está en el documento. Si no alcanza,
lo dice explícitamente en vez de inventar.

## Correr con Docker

```bash
docker compose up --build
```

Queda en http://localhost:8000 (la web en `/`, la doc de la API en
`/docs`).

La base vive en el volumen `docqa-data`, así que el historial sobrevive a
reinicios del contenedor.

## Cómo funciona el asistente

- Al subir el documento se extrae el texto y se corta en chunks con
  solape de oraciones.
- En cada pregunta se arma un índice TF-IDF sobre los chunks y se agarran
  los `top_k` más parecidos.
- Si ni el mejor chunk pasa `MIN_SIMILARITY`, responde de una que el
  documento no tiene la respuesta.
- Si hay contexto suficiente, hay dos modos:

  - **Extractivo** (default, no necesita ninguna key): la respuesta se
    compone con las oraciones más cercanas a la pregunta, citadas tal
    cual. Como es texto literal del documento, no puede inventar.
  - **OpenAI**: con `OPENAI_API_KEY` se mandan los chunks al LLM con un
    prompt que le prohíbe usar conocimiento externo. `OPENAI_BASE_URL`
    sirve para endpoints compatibles (Ollama, Azure, etc.).

Para usar OpenAI en Docker hay que pasar la key como variable de entorno
(o en un `.env` en la raíz, compose lo lee solo):

```bash
# linux/mac
export OPENAI_API_KEY=sk-...
# windows (powershell)
$env:OPENAI_API_KEY="sk-..."

docker compose up --build
```

## Desarrollo local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # en linux/mac: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

El front se sirve desde `frontend/` automáticamente (se puede cambiar con
`FRONTEND_DIR`). Las env vars también se pueden poner en `backend/.env` —
la lista completa está en `.env.example`.

## API

| Método | Ruta                    | Qué hace                                   |
|--------|-------------------------|--------------------------------------------|
| POST   | `/documents`            | Sube documento (multipart, campo `file`)   |
| GET    | `/documents`            | Lista lo cargado                           |
| DELETE | `/documents/{id}`       | Borra un documento y sus chunks            |
| POST   | `/ask`                  | `{session_id, question}` → respuesta       |
| GET    | `/history/{session_id}` | Mensajes de la sesión                      |
| GET    | `/health`               | Estado + modo de asistente                 |

Ejemplo rápido (hay un doc de prueba en `examples/`):

```bash
curl -F "file=@examples/manual_politicas.txt" http://localhost:8000/documents

curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"session_id\": \"demo\", \"question\": \"¿Cuántos días de vacaciones hay?\"}"

curl http://localhost:8000/history/demo
```

(en bash el `-d` va con comillas simples: `-d '{"session_id": ...}'`)

## Tests y lint

```bash
cd backend
pytest                  # unitarios + integración
pytest --cov=app        # con cobertura
ruff check .
ruff format --check .   # compatible con black
```

Los de integración cubren el flujo entero (subir doc → preguntar →
historial) más los errores: extensión no soportada, doc vacío, preguntar
sin documento, inputs inválidos.

## Estructura

```
backend/app/
  domain/          entidades, puertos (Protocol), errores de negocio
  application/     casos de uso
  infrastructure/  sqlalchemy, tfidf, extractivo, openai, loader de archivos
  api/             routers, schemas pydantic, mapeo de errores, DI
frontend/          SPA (index.html + app.js + styles.css)
```

Las capas hablan por los puertos del dominio: cambiar SQLite por Postgres,
TF-IDF por embeddings o el proveedor de LLM no toca la lógica de negocio.
El porqué de cada decisión está en [DECISION_LOG.md](DECISION_LOG.md).

## Limitaciones honestas

- Sin `OPENAI_API_KEY` las respuestas son citas literales: correctas pero
  menos "naturales" que lo que diría un LLM.
- El índice se reconstruye en cada pregunta. Con cientos de chunks es
  instantáneo; si el corpus crece hay que cachearlo.
- `/history/{session_id}` devuelve lista vacía para sesiones sin mensajes
  en vez de 404 (el porqué está en el decision log).
