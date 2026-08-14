from dataclasses import dataclass
from pathlib import Path

from unstructured.partition.pdf import partition_pdf

from ingestion.pdf_loader import RENDER_DPI

# unstructured element categories -> our region types. Anything not listed is "text".
REGION_TYPE_MAP = {
    "Table": "table",
    "Image": "figure",
}


@dataclass
class Region:
    page_number: int
    region_type: str  # "text" | "table" | "figure"
    bbox: tuple[float, float, float, float]
    text: str
    order: int
    category: str  # raw unstructured category, kept for debugging


def detect_layout(pdf_path: Path) -> list[Region]:
    """Partition a PDF into layout regions (text/table/figure) with pixel bboxes
    aligned to pdf_loader's RENDER_DPI, so they overlay directly on rendered pages."""
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="hi_res",
        pdf_image_dpi=RENDER_DPI,
        infer_table_structure=True,
    )

    regions: list[Region] = []
    for order, el in enumerate(elements):
        coords = el.metadata.coordinates
        if coords is None:
            continue
        xs = [p[0] for p in coords.points]
        ys = [p[1] for p in coords.points]
        bbox = (min(xs), min(ys), max(xs), max(ys))

        category = el.category
        region_type = REGION_TYPE_MAP.get(category, "text")

        if region_type == "table":
            text = getattr(el.metadata, "text_as_html", None) or str(el)
        else:
            text = str(el)

        regions.append(
            Region(
                page_number=el.metadata.page_number,
                region_type=region_type,
                bbox=bbox,
                text=text,
                order=order,
                category=category,
            )
        )
    return regions
