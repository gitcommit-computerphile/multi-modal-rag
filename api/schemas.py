from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentStatusResponse(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int | None
    pages_done: int
    pages_total: int | None
    current_step: str | None
    error_message: str | None


class DocumentListItem(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int | None
    uploaded_at: datetime


class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None
    top_k: int = 5


class Citation(BaseModel):
    chunk_id: str
    page_number: int


class QueryResponse(BaseModel):
    answer_text: str
    citations: list[Citation]
    retrieved_chunk_ids: list[str]


class CreateSessionRequest(BaseModel):
    title: str | None = None
    document_id: str | None = None


class SessionResponse(BaseModel):
    id: str
    title: str
    document_id: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[Citation] | None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    document_id: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    question: str
    document_id: str | None = None
    top_k: int = 5
