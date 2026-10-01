# Decisiones técnicas

Acá dejo anotadas las decisiones que fui tomando, qué descarté y por qué.
Si algo del código no se entiende, probablemente acá está la respuesta.

## Asistente: extractivo local + OpenAI opcional

El enunciado pedía que el asistente no invente, así que armé dos
implementaciones del mismo puerto (`AssistantEngine`):

- `ExtractiveAssistant` es el que corre por defecto. Recupera los chunks
  con TF-IDF y arma la respuesta juntando las oraciones del documento más
  parecidas a la pregunta, tal cual están escritas. Como cita texto literal
  no hay forma de que alucine, y la app anda en docker sin configurar nada.
- `OpenAIAssistant` se activa con `OPENAI_API_KEY`. Los mismos chunks van
  como contexto con un system prompt que le prohíbe salirse del documento.
  Con `OPENAI_BASE_URL` sirve para Ollama o cualquier endpoint compatible.

Descarté:

- Pedir una API key sí o sí: le suma fricción al que evalúa, y si no la
  tiene no puede probar la app.
- Embeddings + base vectorial (pgvector, qdrant): para un documento de
  pocas páginas es matar moscas a cañonazos y encima agranda mucho la
  imagen de docker.
- LangChain y similares: demasiada abstracción para lo que al final son
  dos llamadas concretas.

## Retrieval: TF-IDF escrito a mano

Son ~50 líneas de TF-IDF + similitud coseno, con normalización de tildes y
stopwords en español. Para el volumen de texto que maneja esto alcanza y
sobra, y no meto dependencias pesadas tipo scikit-learn o faiss.

El punto de extensión es el `Retriever` (Protocol): el caso de uso recibe
un `retriever_factory`, así que pasar a embeddings es cambiar una línea en
`deps.py` y listo, sin tocar dominio ni aplicación.

## SQLite + SQLAlchemy async

SQLite porque es un desafío acotado y compose tiene que levantar todo con
un comando, sin servicios extra. `DATABASE_URL` acepta cualquier URL async
de SQLAlchemy, así que pasar a Postgres sería cambiar una env var nomás
(ej. `postgresql+asyncpg://...`).

Ojo: usé `create_all` en el lifespan en vez de Alembic. Con tres tablas y
una sola persona escribiendo, las migraciones eran ceremonia gratis.

## Capas

- `domain`: entidades (dataclasses), puertos (`Protocol`) y excepciones
- `application`: casos de uso
- `infrastructure`: sqlalchemy, tfidf, extractivo, cliente openai, loader
- `api`: routers, schemas pydantic, mapeo de errores, DI

Las dependencias siempre apuntan hacia el dominio. Nada de infraestructura
se cuela para arriba.

## Errores

Excepciones de dominio (`AppError` y subclases) mapeadas a HTTP en un solo
lugar (`api/errors.py`):

- 415 extensión no soportada
- 413 tamaño excedido
- 422 documento vacío / input inválido
- 409 preguntar sin documento cargado
- 502 si el proveedor de IA externo falla

Sobre `/history/{session_id}`: devuelve 200 con lista vacía si la sesión
no tiene mensajes, no 404. El session_id lo genera el cliente (un uuid en
el front), o sea que no existe un recurso "sesión" persistido que pueda o
no estar; devolver 404 sería medio mentiroso.

## Fechas

Los `created_at` se guardan en UTC. Ojo con esto: sqlite devuelve los
datetimes naive (sin zona horaria) y el navegador interpretaba el ISO
pelado como hora local, así que las horas salían corridas. Por eso en el
repositorio se marca el tz como UTC al leer, y el JSON sale con la Z al
final que el front sí parsea bien.

## Borrar y re-subir documentos

`DELETE /documents/{id}` borra el doc con sus chunks. Además, subir un
archivo con el mismo nombre que uno existente lo reemplaza: probando me
di cuenta de que sin eso el corpus acumulaba versiones viejas y las
respuestas salían del documento anterior.

## Frontend vanilla

HTML/CSS/JS sin build ni framework. Para una sola pantalla (subir doc +
chat + historial) React era overkill: sumaba toolchain sin ganancia.
FastAPI sirve `/` como estático así que un solo contenedor resuelve todo y
de yapa no hay que pelear con CORS (igual quedó configurable por las dudas).

## Ruff para todo

Lint + orden de imports (reglas `I`, equivalente a isort) + formato
(`ruff format`, compatible con black). Una sola herramienta en vez de tres
que se pisen entre sí.

Ignoré `B008` porque es un falso positivo con `Depends()`/`File()` (es el
patrón idiomático de FastAPI) y `E501` porque el largo de línea lo controla
el formatter.

## El índice se arma en cada request

Cada `/ask` levanta los chunks de la base y construye el TF-IDF de nuevo.
Con cientos de chunks tarda menos de 1ms y me ahorro todo el problema de
invalidación de cache. Si el corpus creciera mucho la idea es cachearlo en
`app.state` e invalidarlo al subir documentos (quedó anotado como TODO en
el caso de uso).

## Si tuviera más tiempo

- streaming de la respuesta (SSE). Solo tendría sentido con el modo LLM,
  en extractivo la respuesta es instantánea
- Alembic + Postgres en compose si esto fuera a producción
- auth: hoy el session_id lo genera el cliente, cualquiera que lo adivine
  puede leer ese historial
- paginación del historial
- stemming o sinónimos en el retrieval: hoy "remoto" no matchea con
  "home office" aunque hablan de lo mismo
- deploy en railway/fly.io (era opcional)
