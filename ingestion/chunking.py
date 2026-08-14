from dataclasses import dataclass


@dataclass
class Chunk:
    doc_id: str
    page_number: int
    chunk_index: int
    source_type: str  # "text" | "table" | "figure"
    bbox: tuple[float, float, float, float]
    content: str
    section_title: str = ""
    parent_page_image: str = ""
    crop_image: str = ""


def chunk_regions(doc_id: str, regions: list, page_images: dict) -> list[Chunk]:
    """Convert layout regions into layout-aware chunks.

    Args:
        doc_id: document identifier
        regions: list of Region objects from layout detection
        page_images: dict mapping page_number -> page image path

    Returns:
        list of Chunk objects
    """
    chunks: list[Chunk] = []
    chunk_index = 0

    for region in regions:
        page_num = region.page_number
        page_img_path = str(page_images.get(page_num, ""))

        # Split oversized regions at sentence/row boundaries if needed
        # For now, treat each region as one chunk
        sub_chunks = _split_if_oversized(region)

        for sub_chunk in sub_chunks:
            chunk = Chunk(
                doc_id=doc_id,
                page_number=page_num,
                chunk_index=chunk_index,
                source_type=sub_chunk["type"],
                bbox=sub_chunk["bbox"],
                content=sub_chunk["text"],
                parent_page_image=page_img_path,
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


def _split_if_oversized(region, max_tokens: int = 800) -> list[dict]:
    """Split a region if it's oversized, at natural boundaries."""
    text = region.text
    # Rough estimate: ~4 chars per token
    est_tokens = len(text) // 4

    if est_tokens <= max_tokens:
        return [{"type": region.region_type, "text": text, "bbox": region.bbox}]

    # For tables, split at row boundaries (naive approach: split on \n)
    if region.region_type == "table":
        lines = text.split("\n")
        chunks_out = []
        current = []
        current_tokens = 0

        for line in lines:
            line_tokens = len(line) // 4
            if current_tokens + line_tokens > max_tokens and current:
                chunks_out.append("\n".join(current))
                current = [line]
                current_tokens = line_tokens
            else:
                current.append(line)
                current_tokens += line_tokens

        if current:
            chunks_out.append("\n".join(current))

        return [
            {"type": region.region_type, "text": c, "bbox": region.bbox}
            for c in chunks_out
        ]

    # For text, split on sentence boundaries
    sentences = text.replace(".", ".\n").split("\n")
    chunks_out = []
    current = []
    current_tokens = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        sent_tokens = len(sent) // 4
        if current_tokens + sent_tokens > max_tokens and current:
            chunks_out.append(" ".join(current))
            current = [sent]
            current_tokens = sent_tokens
        else:
            current.append(sent)
            current_tokens += sent_tokens

    if current:
        chunks_out.append(" ".join(current))

    return [
        {"type": region.region_type, "text": c, "bbox": region.bbox}
        for c in chunks_out
    ]
