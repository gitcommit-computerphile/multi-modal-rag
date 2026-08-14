from pathlib import Path

from ingestion.chunking import chunk_regions
from ingestion.embedding import embed_chunks
from ingestion.layout import detect_layout
from ingestion.pdf_loader import render_pdf
from storage.file_store import FileStore


def run_ingestion(pdf_path: Path, doc_id: str) -> list:
    """End-to-end ingestion: render, parse layout, chunk, embed.

    Returns list of Chunk objects ready for DB storage.
    """
    store = FileStore()
    pages_dir = Path("data/pages") / doc_id

    # M1: Render PDF pages
    print(f"[1/5] Rendering {pdf_path}...")
    page_renders = render_pdf(pdf_path, pages_dir)
    page_images = {p.page_number: p.image_path for p in page_renders}

    print(f"[2/5] Detecting layout in {len(page_renders)} pages...")
    regions = detect_layout(pdf_path)
    print(f"  Found {len(regions)} regions (text/table/figure)")

    # M3: Chunk regions (layout-aware, not fixed-window)
    print("[3/5] Creating chunks from regions...")
    chunks = chunk_regions(doc_id, regions, page_images)
    print(f"  Created {len(chunks)} chunks")

    # M3: Embed chunks
    print("[4/5] Embedding chunks...")
    chunks = embed_chunks(chunks)

    # Save page images to storage
    print("[5/5] Saving page images...")
    for page_num, page_path in page_images.items():
        img_bytes = page_path.read_bytes()
        store.save_page(doc_id, page_num, img_bytes)

    return chunks
