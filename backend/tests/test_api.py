import io


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_upload_document(client):
    res = client.post(
        "/documents",
        files={"file": ("doc.txt", b"Hola mundo, esto es un test.", "text/plain")},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["filename"] == "doc.txt"
    assert body["chunk_count"] >= 1

    docs = client.get("/documents").json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "doc.txt"


def test_upload_unsupported_extension(client):
    res = client.post(
        "/documents",
        files={"file": ("virus.exe", b"MZ...", "application/octet-stream")},
    )
    assert res.status_code == 415


def test_upload_empty_document(client):
    res = client.post(
        "/documents",
        files={"file": ("vacio.txt", b"   \n  ", "text/plain")},
    )
    assert res.status_code == 422


def test_ask_without_document_returns_409(client):
    res = client.post("/ask", json={"session_id": "s1", "question": "¿algo?"})
    assert res.status_code == 409


def test_full_flow_ask_and_history(client_with_doc):
    client = client_with_doc
    res = client.post(
        "/ask",
        json={
            "session_id": "sesion-1",
            "question": "¿Cuántos días de vacaciones tengo?",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "15" in body["answer"]
    assert body["sources"]
    assert body["sources"][0]["document"] == "politicas.txt"

    res = client.post(
        "/ask",
        json={"session_id": "sesion-1", "question": "¿Cuándo se paga el bono?"},
    )
    assert res.status_code == 200
    assert "diciembre" in res.json()["answer"].lower()

    history = client.get("/history/sesion-1").json()
    assert history["session_id"] == "sesion-1"
    assert [m["role"] for m in history["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert "vacaciones" in history["messages"][0]["content"]


def test_history_is_scoped_by_session(client_with_doc):
    client = client_with_doc
    client.post("/ask", json={"session_id": "a", "question": "¿días de vacaciones?"})
    client.post("/ask", json={"session_id": "b", "question": "¿home office?"})

    hist_a = client.get("/history/a").json()["messages"]
    hist_b = client.get("/history/b").json()["messages"]
    hist_c = client.get("/history/sin-mensajes").json()["messages"]

    assert len(hist_a) == 2
    assert len(hist_b) == 2
    assert hist_c == []


def test_question_outside_document_does_not_invent(client_with_doc):
    res = client_with_doc.post(
        "/ask",
        json={
            "session_id": "s",
            "question": "¿Cuál es la capital de Francia?",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "no encontré" in body["answer"].lower()
    assert body["sources"] == []


def test_ask_validates_input(client_with_doc):
    assert client_with_doc.post("/ask", json={"session_id": "", "question": "hola"}).status_code == 422
    assert client_with_doc.post("/ask", json={"session_id": "s", "question": " "}).status_code == 422
    assert client_with_doc.post("/ask", json={"question": "hola"}).status_code == 422


def test_upload_pdf(client):
    # PDF mínimo válido generado a mano
    pdf = _minimal_pdf("contrato de prueba con texto legible")
    res = client.post(
        "/documents",
        files={"file": ("doc.pdf", pdf, "application/pdf")},
    )
    assert res.status_code == 201


def _minimal_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
        b"<</Length " + str(len(stream)).encode() + b">>\nstream\n" + stream + b"\nendstream",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj".encode() + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += (f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF").encode()
    return io.BytesIO(pdf).getvalue()
