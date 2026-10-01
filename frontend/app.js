const sessionLabel = document.getElementById("session-label");
const fileInput = document.getElementById("file-input");
const fileDrop = document.getElementById("file-drop");
const fileDropLabel = document.getElementById("file-drop-label");
const uploadStatus = document.getElementById("upload-status");
const docList = document.getElementById("doc-list");
const messagesEl = document.getElementById("messages");
const emptyState = document.getElementById("empty-state");
const askForm = document.getElementById("ask-form");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");
const errorBanner = document.getElementById("error-banner");
const newSessionBtn = document.getElementById("new-session");

let sessionId = loadSession();
let loading = false;

function loadSession() {
  let id = localStorage.getItem("docqa_session");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("docqa_session", id);
  }
  return id;
}

function setSession(id) {
  sessionId = id;
  localStorage.setItem("docqa_session", id);
  sessionLabel.textContent = id.slice(0, 8) + "…";
}

function showError(text) {
  errorBanner.textContent = text;
  errorBanner.hidden = false;
  setTimeout(() => (errorBanner.hidden = true), 6000); // se cierra solo a los 6s
}

async function apiError(res) {
  try {
    const body = await res.json();
    return body.detail || `Error ${res.status}`;
  } catch {
    return `Error ${res.status}`;
  }
}

/* ---------- documentos ---------- */

async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  uploadStatus.className = "status";
  uploadStatus.textContent = "Subiendo…";

  try {
    const res = await fetch("/documents", { method: "POST", body: form });
    if (!res.ok) throw new Error(await apiError(res));
    const doc = await res.json();
    uploadStatus.className = "status ok";
    uploadStatus.textContent = `Listo: ${doc.chunk_count} fragmentos indexados.`;
    loadDocuments();
  } catch (err) {
    uploadStatus.className = "status err";
    uploadStatus.textContent = err.message;
  }
}

async function loadDocuments() {
  try {
    const res = await fetch("/documents");
    if (!res.ok) return;
    const docs = await res.json();
    docList.innerHTML = "";
    for (const doc of docs) {
      const li = document.createElement("li");
      const kb = (doc.size_bytes / 1024).toFixed(1);
      li.innerHTML = `<strong>${escapeHtml(doc.filename)}</strong>
        <div class="meta">${kb} KB · ${doc.chunk_count} chunks</div>`;
      docList.appendChild(li);
    }
  } catch {
    /* la lista es decorativa, no molestamos al usuario */
  }
}

/* ---------- chat ---------- */

function addMessage(role, content, sources = [], time = null) {
  emptyState.style.display = "none";
  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const text = document.createElement("div");
  text.textContent = content;
  div.appendChild(text);

  if (sources.length) {
    const details = document.createElement("details");
    details.className = "sources";
    const summary = document.createElement("summary");
    summary.textContent = `${sources.length} fragmento(s) del documento`;
    details.appendChild(summary);
    for (const s of sources) {
      const p = document.createElement("p");
      p.textContent = `${s.document}: “${s.snippet}”`;
      details.appendChild(p);
    }
    div.appendChild(details);
  }

  const stamp = document.createElement("span");
  stamp.className = "time";
  stamp.textContent = (time ? new Date(time) : new Date()).toLocaleTimeString();
  div.appendChild(stamp);

  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

async function ask(question) {
  loading = true;
  sendBtn.disabled = true;
  questionInput.disabled = true;
  const pending = addMessage("assistant loading", "Pensando…");

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question }),
    });
    if (!res.ok) throw new Error(await apiError(res));
    const data = await res.json();
    pending.remove();
    addMessage("assistant", data.answer, data.sources, data.created_at);
  } catch (err) {
    pending.remove();
    addMessage("assistant", "Ups, algo salió mal. " + err.message);
  } finally {
    loading = false;
    sendBtn.disabled = false;
    questionInput.disabled = false;
    questionInput.focus();
  }
}

async function loadHistory() {
  messagesEl.querySelectorAll(".msg").forEach((m) => m.remove());
  try {
    const res = await fetch(`/history/${sessionId}`);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.messages.length) {
      emptyState.style.display = "";
      return;
    }
    for (const m of data.messages) {
      addMessage(m.role, m.content, m.sources, m.created_at);
    }
  } catch {
    /* sin historial disponible, se empieza de cero */
  }
}

/* ---------- eventos ---------- */

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) uploadDocument(fileInput.files[0]);
  fileInput.value = "";
});

fileDrop.addEventListener("dragover", (e) => {
  e.preventDefault();
  fileDrop.classList.add("dragover");
});

fileDrop.addEventListener("dragleave", () =>
  fileDrop.classList.remove("dragover")
);

fileDrop.addEventListener("drop", (e) => {
  e.preventDefault();
  fileDrop.classList.remove("dragover");
  if (e.dataTransfer.files[0]) uploadDocument(e.dataTransfer.files[0]);
});

askForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question || loading) return;
  addMessage("user", question);
  questionInput.value = "";
  ask(question);
});

newSessionBtn.addEventListener("click", () => {
  setSession(crypto.randomUUID());
  loadHistory();
});

/* ---------- init ---------- */

setSession(sessionId);
loadDocuments();
loadHistory();
