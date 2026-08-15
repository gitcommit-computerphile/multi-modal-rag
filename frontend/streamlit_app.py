import time

import requests
import streamlit as st

# 127.0.0.1, not localhost: on Windows "localhost" resolves to IPv6 ::1 first while
# uvicorn binds IPv4, costing a ~2s failed-connect timeout on every single request.
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Multimodal Document RAG",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      #MainMenu, footer, header {visibility: hidden;}

      .block-container {padding-top: 2.4rem; padding-bottom: 7rem; max-width: 1080px;}

      /* ---- Sidebar ---- */
      section[data-testid="stSidebar"] {
          background: #10141C;
          border-right: 1px solid #222836;
      }
      section[data-testid="stSidebar"] .block-container {padding-top: 1.6rem;}

      .side-head {
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #6B7688;
          margin: 1.4rem 0 0.5rem 0.2rem;
      }

      /* Inactive chat rows: flat and muted */
      section[data-testid="stSidebar"] button[kind="tertiary"],
      section[data-testid="stSidebar"] button[data-testid="stBaseButton-tertiary"] {
          text-align: left !important;
          justify-content: flex-start !important;
          font-weight: 400 !important;
          color: #A3AEC2 !important;
          background: transparent !important;
          border: 1px solid transparent !important;
          border-radius: 8px;
          padding: 0.42rem 0.6rem !important;
      }
      section[data-testid="stSidebar"] button[kind="tertiary"]:hover,
      section[data-testid="stSidebar"] button[data-testid="stBaseButton-tertiary"]:hover {
          background: #1A2130 !important;
          color: #E6EAF2 !important;
      }

      /* Active chat row: accent highlight */
      section[data-testid="stSidebar"] button[kind="secondary"],
      section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
          text-align: left !important;
          justify-content: flex-start !important;
          font-weight: 600 !important;
          color: #FFFFFF !important;
          background: rgba(124, 108, 255, 0.16) !important;
          border: 1px solid rgba(124, 108, 255, 0.45) !important;
          border-radius: 8px;
          padding: 0.42rem 0.6rem !important;
      }

      section[data-testid="stSidebar"] .stButton > button p {
          font-size: 0.87rem;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
      }

      /* ---- Headings ---- */
      .app-title {
          font-size: 2rem;
          font-weight: 700;
          letter-spacing: -0.025em;
          background: linear-gradient(92deg, #FFFFFF 10%, #9C90FF 95%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 0.25rem;
      }
      .app-sub {
          color: #8A94A6;
          font-size: 0.95rem;
          margin-bottom: 1.8rem;
          max-width: 640px;
      }

      .doc-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          background: #171D2A;
          border: 1px solid #262E3E;
          border-radius: 999px;
          padding: 0.3rem 0.85rem;
          font-size: 0.8rem;
          color: #A3AEC2;
          margin-bottom: 1.4rem;
      }
      .doc-chip::before {
          content: "";
          width: 6px; height: 6px;
          border-radius: 50%;
          background: #22C55E;
      }

      /* ---- Landing cards ---- */
      .card {
          border: 1px solid #232B3A;
          border-radius: 14px;
          padding: 1.3rem 1.5rem 1.4rem;
          background: linear-gradient(180deg, #151B27 0%, #121722 100%);
      }
      .card h4 {margin: 0 0 0.3rem 0; font-size: 1.03rem; color: #E6EAF2;}
      .card p {margin: 0; color: #7E8899; font-size: 0.85rem;}

      .src-meta {
          font-size: 0.76rem;
          color: #8A94A6;
          margin-top: 0.4rem;
      }
      .src-meta code {
          background: #1B2230;
          padding: 0.05rem 0.35rem;
          border-radius: 4px;
          color: #9C90FF;
      }

      div[data-testid="stChatMessage"] {
          background: transparent;
          padding: 0.3rem 0;
      }

      div[data-testid="stExpander"] details {
          border: 1px solid #232B3A;
          border-radius: 10px;
          background: #131926;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- API helpers ----------

@st.cache_resource
def http():
    """One pooled connection reused across reruns. A fresh connection per call
    costs ~20ms each; reusing one drops it to ~2ms."""
    s = requests.Session()
    s.mount("http://", requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=8))
    return s


def api_get(path):
    resp = http().get(f"{API_URL}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def doc_label(doc):
    pages = f"{doc['page_count']}p" if doc.get("page_count") else "?"
    return f"{doc['filename']}  ·  {pages}"


def reset_to_landing():
    for key in (
        "active_session_id",
        "current_session",
        "pending_doc_id",
        "pending_doc_status",
        "uploaded_file_id",
    ):
        st.session_state.pop(key, None)
    st.session_state.active_session_id = None


def start_session(document_id):
    resp = http().post(
        f"{API_URL}/sessions/", json={"document_id": document_id}, timeout=30
    )
    resp.raise_for_status()
    new_session = resp.json()
    st.session_state.active_session_id = new_session["id"]
    st.session_state.current_session = api_get(f"/sessions/{new_session['id']}")
    st.rerun()


if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

try:
    documents = api_get("/documents/")
    api_online = True
except Exception:
    documents = []
    api_online = False

doc_names = {d["id"]: d["filename"] for d in documents}


# ---------- Sidebar ----------

with st.sidebar:
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:700;letter-spacing:-0.01em;'>"
        "Document RAG</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    if st.button("＋  New chat", use_container_width=True, type="primary"):
        reset_to_landing()
        st.rerun()

    st.markdown("<div class='side-head'>Conversations</div>", unsafe_allow_html=True)

    if not api_online:
        st.error("API offline")
        sessions = []
    else:
        try:
            sessions = api_get("/sessions/")
        except Exception as e:
            sessions = []
            st.error(f"Could not load chats: {e}")

    if not sessions:
        st.caption("No conversations yet.")

    for s in sessions:
        is_active = s["id"] == st.session_state.active_session_id
        row = st.columns([6, 1], gap="small")
        if row[0].button(
            s["title"] or "New chat",
            key=f"open_{s['id']}",
            use_container_width=True,
            type="secondary" if is_active else "tertiary",
        ):
            st.session_state.active_session_id = s["id"]
            st.session_state.current_session = api_get(f"/sessions/{s['id']}")
            st.rerun()
        if row[1].button("✕", key=f"del_{s['id']}", help="Delete", type="tertiary"):
            http().delete(f"{API_URL}/sessions/{s['id']}", timeout=30)
            if st.session_state.active_session_id == s["id"]:
                reset_to_landing()
            st.rerun()


# ---------- Sources ----------

def render_sources(citations):
    if not citations:
        return

    unique, seen = [], set()
    for c in citations:
        if c["chunk_id"] not in seen:
            seen.add(c["chunk_id"])
            unique.append(c)

    with st.expander(f"Sources · {len(unique)} regions from the page"):
        cols = st.columns(min(len(unique), 3))
        for i, cite in enumerate(unique):
            with cols[i % 3]:
                st.image(
                    f"{API_URL}/chunks/{cite['chunk_id']}/preview?crop=true",
                    use_container_width=True,
                )
                st.markdown(
                    f"<div class='src-meta'>Page {cite['page_number']} · "
                    f"<code>{cite['chunk_id'][:8]}</code></div>",
                    unsafe_allow_html=True,
                )


# ---------- Main ----------

if not api_online:
    st.markdown("<div class='app-title'>Multimodal Document RAG</div>", unsafe_allow_html=True)
    st.error(
        "Cannot reach the API at http://localhost:8000. Start it with "
        "`python -m uvicorn api.main:app --reload` and make sure Postgres is running."
    )
    st.stop()

if st.session_state.active_session_id is None:
    st.markdown("<div class='app-title'>Multimodal Document RAG</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='app-sub'>Ask questions about PDFs with real tables and charts. "
        "Every answer is grounded in the page image itself, not just extracted text.</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(
            "<div class='card'><h4>Upload a document</h4>"
            "<p>PDFs with tables or charts work best.</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf", label_visibility="collapsed")

        if uploaded_file and st.session_state.get("uploaded_file_id") != uploaded_file.file_id:
            try:
                resp = http().post(
                    f"{API_URL}/documents/", files={"file": uploaded_file}, timeout=120
                )
                if resp.status_code == 200:
                    st.session_state.pending_doc_id = resp.json()["document_id"]
                    st.session_state.pending_doc_status = "pending"
                    st.session_state.uploaded_file_id = uploaded_file.file_id
                else:
                    st.error(f"Upload failed: {resp.status_code} {resp.text}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

        pending_id = st.session_state.get("pending_doc_id")
        if pending_id and st.session_state.get("pending_doc_status") != "ingested":
            with st.status("Processing document...", expanded=True) as box:
                last_step = None
                for _ in range(300):
                    try:
                        info = api_get(f"/documents/{pending_id}")
                    except Exception as e:
                        box.update(label="Status check failed", state="error")
                        st.error(str(e))
                        break

                    step = info.get("current_step")
                    if step and step != last_step:
                        st.write(step)
                        last_step = step

                    if info["status"] == "ingested":
                        box.update(label="Document ready", state="complete", expanded=False)
                        st.session_state.pending_doc_status = "ingested"
                        break
                    if info["status"] == "failed":
                        box.update(label="Ingestion failed", state="error")
                        st.error(info.get("error_message") or "See API logs.")
                        st.session_state.pending_doc_status = "failed"
                        break
                    time.sleep(0.6)

        if st.session_state.get("pending_doc_status") == "ingested":
            st.success("Document ready.")
            if st.button("Start chatting", type="primary", use_container_width=True):
                start_session(pending_id)
        elif st.session_state.get("pending_doc_status") == "failed":
            st.error("Ingestion failed. Check the API server logs.")

    with right:
        st.markdown(
            "<div class='card'><h4>Or pick an existing one</h4>"
            "<p>Already ingested and ready to query.</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        ready_docs = [d for d in documents if d["status"] == "ingested"]
        if not ready_docs:
            st.caption("Nothing ingested yet.")
        else:
            choice = st.selectbox(
                "Existing document",
                options=[d["id"] for d in ready_docs],
                format_func=lambda i: doc_label(next(d for d in ready_docs if d["id"] == i)),
                label_visibility="collapsed",
            )
            if st.button(
                "Start chatting", key="existing_start", type="primary", use_container_width=True
            ):
                start_session(choice)

else:
    session = st.session_state.get("current_session") or api_get(
        f"/sessions/{st.session_state.active_session_id}"
    )

    st.markdown(
        f"<div class='app-title'>{session['title'] or 'New chat'}</div>",
        unsafe_allow_html=True,
    )
    doc_id = session.get("document_id")
    st.markdown(
        f"<div class='doc-chip'>{doc_names.get(doc_id, doc_id or 'no document')}</div>",
        unsafe_allow_html=True,
    )

    if not session["messages"]:
        st.caption("Ask something about this document to get started.")

    for msg in session["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_sources(msg.get("citations"))

    question = st.chat_input("Ask about this document...")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.chat_message("assistant"), st.spinner("Reading the pages..."):
                resp = http().post(
                    f"{API_URL}/sessions/{st.session_state.active_session_id}/messages",
                    json={"question": question, "top_k": 5},
                    timeout=180,
                )
            if resp.status_code == 200:
                st.session_state.current_session = api_get(
                    f"/sessions/{st.session_state.active_session_id}"
                )
                st.rerun()
            else:
                st.error(f"Query failed: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Query failed: {e}")
