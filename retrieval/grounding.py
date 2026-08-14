from storage.file_store import FileStore


def load_page_images(context_chunks: list) -> list[dict]:
    """Load page images for top-k chunks for visual grounding."""
    store = FileStore()
    page_images = {}

    for chunk in context_chunks:
        key = (chunk["document_id"], chunk["page_number"])
        if key not in page_images:
            img_bytes = store.load_page(chunk["document_id"], chunk["page_number"])
            if img_bytes:
                page_images[key] = {
                    "doc_id": chunk["document_id"],
                    "page_number": chunk["page_number"],
                    "image_bytes": img_bytes,
                }

    return list(page_images.values())
