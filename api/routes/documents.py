from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.schemas import DocumentStatusResponse, DocumentUploadResponse
from db.models import Chunk as ChunkRow
from db.models import Document, IngestionJob
from db.session import get_session
from ingestion.pipeline import run_ingestion
from storage.file_store import FileStore

router = APIRouter(prefix="/documents", tags=["documents"])


def _run_ingestion_job(doc_id: str, job_id: str, pdf_path: str) -> None:
    """Runs the ingestion pipeline and updates document/job status. Called as a background task."""
    session = get_session()
    doc = session.query(Document).filter(Document.id == doc_id).first()
    job = session.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    doc.status = "processing"
    job.status = "running"
    session.commit()

    try:
        chunks = run_ingestion(Path(pdf_path), doc_id)

        for chunk in chunks:
            session.add(
                ChunkRow(
                    id=str(uuid4()),
                    document_id=chunk.doc_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    source_type=chunk.source_type,
                    bbox=list(chunk.bbox),
                    content=chunk.content,
                    parent_page_image=chunk.parent_page_image,
                    crop_image=chunk.crop_image,
                    embedding=chunk.embedding,
                )
            )

        doc.status = "ingested"
        doc.page_count = len({c.page_number for c in chunks})
        job.status = "succeeded"
        job.pages_done = doc.page_count
        job.pages_total = doc.page_count
        session.commit()
    except Exception as e:
        session.rollback()
        doc.status = "failed"
        doc.error_message = str(e)
        job.status = "failed"
        job.error_message = str(e)
        session.commit()
    finally:
        session.close()


@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF and start async ingestion."""
    doc_id = str(uuid4())
    store = FileStore()

    # Save uploaded file
    content = await file.read()
    upload_path = str(store.settings.uploads_dir / f"{doc_id}.pdf")
    store.settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(content)

    # Create DB records
    session = get_session()
    doc = Document(
        id=doc_id,
        filename=file.filename,
        storage_path=upload_path,
        status="pending",
    )
    session.add(doc)
    session.commit()

    job = IngestionJob(document_id=doc_id, status="pending")
    session.add(job)
    session.commit()
    job_id = job.id

    session.close()

    background_tasks.add_task(_run_ingestion_job, doc_id, job_id, upload_path)

    return DocumentUploadResponse(
        document_id=doc_id, job_id=job_id, status="pending"
    )


@router.get("/{doc_id}", response_model=DocumentStatusResponse)
def get_document_status(doc_id: str):
    """Get document and ingestion job status."""
    session = get_session()
    doc = session.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        session.close()
        raise HTTPException(status_code=404, detail="Document not found")

    job = (
        session.query(IngestionJob)
        .filter(IngestionJob.document_id == doc_id)
        .order_by(IngestionJob.created_at.desc())
        .first()
    )

    session.close()

    return DocumentStatusResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        page_count=doc.page_count,
        pages_done=job.pages_done if job else 0,
        pages_total=job.pages_total if job else None,
        error_message=job.error_message if job else None,
    )
