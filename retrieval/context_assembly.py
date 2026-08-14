def assemble_context(chunks: list) -> list[dict]:
    """Expand chunks with parent-page context.

    For each chunk, include nearby chunks on the same page to provide
    surrounding context (especially useful for tables/figures which
    are often explained by nearby text).
    """
    if not chunks:
        return []

    # Group chunks by document and page
    by_doc_page: dict = {}
    for chunk in chunks:
        key = (chunk.document_id, chunk.page_number)
        by_doc_page.setdefault(key, []).append(chunk)

    context_list = []
    seen_ids = set()

    for chunk in chunks:
        if chunk.id in seen_ids:
            continue

        key = (chunk.document_id, chunk.page_number)
        page_chunks = sorted(by_doc_page[key], key=lambda c: c.chunk_index)

        idx = next(i for i, c in enumerate(page_chunks) if c.id == chunk.id)
        nearby = page_chunks[max(0, idx - 1) : min(len(page_chunks), idx + 2)]

        merged_content = " ".join([c.content for c in nearby])
        context_list.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "page_number": chunk.page_number,
                "source_type": chunk.source_type,
                "bbox": chunk.bbox,
                "content": merged_content,
                "primary_chunk_id": chunk.id,
            }
        )
        for c in nearby:
            seen_ids.add(c.id)

    return context_list
