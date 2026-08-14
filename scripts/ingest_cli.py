"""Standalone ingestion CLI for testing the full pipeline."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.models import Chunk
from db.session import get_session, init_db
from ingestion.pipeline import run_ingestion


def ingest_file(pdf_path: str) -> None:
    """Ingest a PDF and store chunks in DB."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    # Initialize DB
    print("Initializing database...")
    init_db()

    doc_id = str(uuid4())
    print(f"Ingesting {pdf_path} with ID {doc_id}...")

    try:
        chunks = run_ingestion(pdf_path, doc_id)
        print(f"Created {len(chunks)} chunks")

        # Store in DB
        print("Storing chunks in database...")
        session = get_session()
        for chunk in chunks:
            db_chunk = Chunk(
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
            session.add(db_chunk)
        session.commit()
        session.close()

        print(f"Success! Ingested {len(chunks)} chunks for doc {doc_id}")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/ingest_cli.py <path-to-pdf>")
        sys.exit(1)
    ingest_file(sys.argv[1])
