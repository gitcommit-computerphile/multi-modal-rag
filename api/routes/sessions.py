from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from api.schemas import (
    CreateSessionRequest,
    MessageResponse,
    QueryResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from db.models import ChatMessage, ChatSession
from db.session import get_session
from retrieval.answer import answer_question

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
def create_session(req: CreateSessionRequest):
    """Create a new chat session, optionally scoped to a document."""
    session = get_session()
    chat = ChatSession(
        id=str(uuid4()),
        title=req.title or "New Chat",
        document_id=req.document_id,
    )
    session.add(chat)
    session.commit()
    resp = SessionResponse(
        id=chat.id,
        title=chat.title,
        document_id=chat.document_id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )
    session.close()
    return resp


@router.get("/", response_model=list[SessionResponse])
def list_sessions():
    """List all chat sessions, most recently updated first."""
    session = get_session()
    chats = session.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    result = [
        SessionResponse(
            id=c.id,
            title=c.title,
            document_id=c.document_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in chats
    ]
    session.close()
    return result


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(session_id: str):
    """Get a chat session with its full message history."""
    session = get_session()
    chat = session.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat:
        session.close()
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    resp = SessionDetailResponse(
        id=chat.id,
        title=chat.title,
        document_id=chat.document_id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
    session.close()
    return resp


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session and all of its messages."""
    session = get_session()
    session.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    deleted = (
        session.query(ChatSession).filter(ChatSession.id == session_id).delete()
    )
    session.commit()
    session.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@router.post("/{session_id}/messages", response_model=QueryResponse)
def send_message(session_id: str, req: SendMessageRequest):
    """Ask a question within a chat session, with prior turns fed to the model as context."""
    session = get_session()
    chat = session.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat:
        session.close()
        raise HTTPException(status_code=404, detail="Session not found")

    prior_messages = (
        session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior_messages]
    is_first_message = len(prior_messages) == 0

    session.add(
        ChatMessage(id=str(uuid4()), session_id=session_id, role="user", content=req.question)
    )

    doc_id = req.document_id or chat.document_id
    result = answer_question(
        question=req.question, doc_id=doc_id, top_k=req.top_k, history=history
    )

    session.add(
        ChatMessage(
            id=str(uuid4()),
            session_id=session_id,
            role="assistant",
            content=result["answer_text"],
            citations=result["citations"],
        )
    )

    if is_first_message and chat.title == "New Chat":
        chat.title = req.question[:60]
    chat.updated_at = datetime.utcnow()

    session.commit()
    session.close()

    return QueryResponse(
        answer_text=result["answer_text"],
        citations=result["citations"],
        retrieved_chunk_ids=result["retrieved_chunk_ids"],
    )
