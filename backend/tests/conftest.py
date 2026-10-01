import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

# doc chiquito para probar el flujo entero sin depender de archivos externos
SAMPLE_DOC = (
    "Política de vacaciones\n\n"
    "Los empleados tienen derecho a 15 días hábiles de vacaciones por año "
    "calendario. Las vacaciones se deben solicitar con al menos 10 días de "
    "anticipación a través del portal de RRHH.\n\n"
    "Los días no utilizados no se acumulan al año siguiente, salvo aprobación "
    "expresa de la gerencia.\n\n"
    "Beneficios\n\n"
    "La empresa ofrece obra social para el empleado y su familia directa. "
    "Además hay un bono anual de performance que se liquida en diciembre.\n\n"
    "Home office\n\n"
    "Se pueden trabajar hasta 3 días por semana de forma remota. Los martes "
    "son días de presencialidad obligatoria para las reuniones de equipo."
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db}")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


@pytest.fixture()
def client_with_doc(client):
    client.post(
        "/documents",
        files={"file": ("politicas.txt", SAMPLE_DOC.encode(), "text/plain")},
    )
    return client
