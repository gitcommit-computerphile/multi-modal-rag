from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

RENDER_DPI = 200


@dataclass
class TextBlock:
    page_number: int
    bbox: tuple[float, float, float, float]
    text: str


@dataclass
class PageRender:
    page_number: int
    image_path: Path
    width: int
    height: int
    text_blocks: list[TextBlock]


def render_pdf(pdf_path: Path, output_dir: Path) -> list[PageRender]:
    """Render every page of a PDF to PNG and extract native text blocks with bboxes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    zoom = RENDER_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)

    pages: list[PageRender] = []
    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            pix = page.get_pixmap(matrix=matrix)
            image_path = output_dir / f"page_{page_number}.png"
            pix.save(image_path)

            text_blocks = []
            for block in page.get_text("blocks"):
                x0, y0, x1, y1, text, *_ = block
                text = text.strip()
                if not text:
                    continue
                # scale native PDF coords (72 dpi) up to the rendered image's pixel space
                scaled_bbox = (x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom)
                text_blocks.append(TextBlock(page_number=page_number, bbox=scaled_bbox, text=text))

            pages.append(
                PageRender(
                    page_number=page_number,
                    image_path=image_path,
                    width=pix.width,
                    height=pix.height,
                    text_blocks=text_blocks,
                )
            )
    return pages
