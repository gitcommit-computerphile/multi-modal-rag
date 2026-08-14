import time

import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Multimodal Document RAG", layout="wide")


def fetch_sessions():
    resp = requests.get(f"{API_URL}/sessions/")
    resp.raise_for_status()
    return resp.json()


def fetch_session_detail(session_id):
    resp = requests.get(f"{API_URL}/sessions/{session_id}")
    resp.raise_for_status()
    return resp.json()


def reset_to_new_chat():
    st.session_state.active_session_id = None
    st.session_state.pop("current_session", None)
    st.session_state.pop("pending_doc_id", None)
    st.session_state.pop("pending_doc_status", None)
    st.session_state.pop("uploaded_file_id", None)


if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

# --- Sidebar: chat list ---
with st.sidebar:
    st.title("Chats")
    if st.button("+ New Chat", use_container_width=True):
        reset_to_new_chat()
        st.rerun()

    st.divider()

    try:
        sessions = fetch_sessions()
    except Exception as e:
        sessions = []
        st.error(f"Could not load chats: {e}")

    for s in sessions:
        row = st.columns([5, 1])
        label = s["title"] or "New Chat"
        if row[0].button(label, key=f"open_{s['id']}", use_container_width=True):
            st.session_state.active_session_id = s["id"]
            st.session_state.current_session = fetch_session_detail(s["id"])
            st.rerun()
        if row[1].button("x", key=f"del_{s['id']}"):
            requests.delete(f"{API_URL}/sessions/{s['id']}")
            if st.session_state.active_session_id == s["id"]:
                reset_to_new_chat()
            st.rerun()

st.title("Multimodal Document RAG")

# --- Main area ---
if st.session_state.active_session_id is None:
    st.header("Start a new chat")
    st.caption("Upload a PDF to begin. A new chat will be created once it's ready to query.")

    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file and st.session_state.get("uploaded_file_id") != uploaded_file.file_id:
        try:
            resp = requests.post(f"{API_URL}/documents/", files={"file": uploaded_file})
            if resp.status_code == 200:
                result = resp.json()
                st.session_state.pending_doc_id = result["document_id"]
                st.session_state.pending_doc_status = "pending"
                st.session_state.uploaded_file_id = uploaded_file.file_id
            else:
                st.error(f"Upload failed: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    if st.session_state.get("pending_doc_id") and st.session_state.get("pending_doc_status") != "ingested":
        with st.spinner("Ingesting document (rendering pages, detecting tables/figures, embedding)..."):
            for _ in range(120):  # up to ~2 minutes
                try:
                    status_resp = requests.get(f"{API_URL}/documents/{st.session_state.pending_doc_id}")
                    status_resp.raise_for_status()
                    status = status_resp.json()["status"]
                except Exception as e:
                    st.error(f"Failed to check ingestion status: {e}")
                    break

                if status == "ingested":
                    st.session_state.pending_doc_status = "ingested"
                    break
                if status == "failed":
                    st.session_state.pending_doc_status = "failed"
                    break
                time.sleep(1)

    if st.session_state.get("pending_doc_status") == "ingested":
        st.success("Document ready.")
        if st.button("Start chatting"):
            create_resp = requests.post(
                f"{API_URL}/sessions/",
                json={"document_id": st.session_state.pending_doc_id},
            )
            create_resp.raise_for_status()
            new_session = create_resp.json()
            st.session_state.active_session_id = new_session["id"]
            st.session_state.current_session = fetch_session_detail(new_session["id"])
            st.rerun()
    elif st.session_state.get("pending_doc_status") == "failed":
        st.error("Ingestion failed for this document. Check the API server logs.")

else:
    session = st.session_state.get("current_session") or fetch_session_detail(
        st.session_state.active_session_id
    )
    st.caption(f"Document: {session.get('document_id') or 'none'}")

    for msg in session["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("citations"):
                cites = ", ".join(
                    f"p.{c['page_number']} ({c['chunk_id'][:8]})" for c in msg["citations"]
                )
                st.caption(f"Sources: {cites}")

    question = st.chat_input("Ask a question about this document...")
    if question:
        with st.chat_message("user"):
            st.write(question)
        try:
            with st.spinner("Thinking..."):
                resp = requests.post(
                    f"{API_URL}/sessions/{st.session_state.active_session_id}/messages",
                    json={"question": question, "top_k": 5},
                )
            if resp.status_code == 200:
                st.session_state.current_session = fetch_session_detail(
                    st.session_state.active_session_id
                )
                st.rerun()
            else:
                st.error(f"Query failed: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Query failed: {e}")
