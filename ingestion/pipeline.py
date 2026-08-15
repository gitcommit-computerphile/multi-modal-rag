from pathlib import Path

from ingestion.chunking import chunk_regions
from ingestion.embedding import embed_chunks
from ingestion.layout import detect_layout
from ingestion.pdf_loader import render_pdf
from storage.file_store import FileStore


def run_ingestion(pdf_path: Path, doc_id: str, progress=None) -> list:
    """End-to-end ingestion: render, parse layout, chunk, embed.

    progress: optional callable(step: str, done: int, total: int) called as each
    stage completes, so callers can surface live status instead of a blank wait.

    Returns list of Chunk objects ready for DB storage.
    """

    def report(step, done, total=5):
        if progress:
            progress(step, done, total)

    store = FileStore()
    pages_dir = Path("data/pages") / doc_id

    report("Rendering pages", 0)
    print(f"[1/5] Rendering {pdf_path}...")
    page_renders = render_pdf(pdf_path, pages_dir)
    page_images = {p.page_number: p.image_path for p in page_renders}

    report(f"Detecting layout in {len(page_renders)} pages", 1)
    print(f"[2/5] Detecting layout in {len(page_renders)} pages...")
    regions = detect_layout(pdf_path)
    print(f"  Found {len(regions)} regions (text/table/figure)")

    report(f"Chunking {len(regions)} regions", 2)
    print("[3/5] Creating chunks from regions...")
    chunks = chunk_regions(doc_id, regions, page_images)
    print(f"  Created {len(chunks)} chunks")

    report(f"Embedding {len(chunks)} chunks", 3)
    print("[4/5] Embedding chunks...")
    chunks = embed_chunks(chunks)

    report("Saving page images", 4)
    print("[5/5] Saving page images...")
    for page_num, page_path in page_images.items():
        img_bytes = page_path.read_bytes()
        store.save_page(doc_id, page_num, img_bytes)

    report("Done", 5)
    return chunks
