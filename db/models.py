from datetime import datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str]
    storage_path: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")  # pending|processing|ingested|failed
    page_count: Mapped[int | None]
    error_message: Mapped[str | None]
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    ingested_at: Mapped[datetime | None]


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")  # pending|running|succeeded|failed
    current_step: Mapped[str | None]
    pages_total: Mapped[int | None]
    pages_done: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str]
    page_number: Mapped[int]
    source_type: Mapped[str]  # text|table|figure
    chunk_index: Mapped[int]
    section_title: Mapped[str | None]
    bbox: Mapped[list | None] = mapped_column(JSON)  # [x0, y0, x1, y1]
    content: Mapped[str]
    parent_page_image: Mapped[str]
    crop_image: Mapped[str | None]
    token_count: Mapped[int | None]
    embedding: Mapped[Vector] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(default="New Chat")
    document_id: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str]
    role: Mapped[str]  # user|assistant
    content: Mapped[str]
    citations: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
