"""Standalone M1 check: render a PDF, detect layout regions, and draw color-coded
bboxes on each page so table/figure/text detection can be visually verified.

Usage: python scripts/debug_layout.py samples/some_filing.pdf
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.layout import detect_layout
from ingestion.pdf_loader import render_pdf

COLORS = {
    "text": "#3B82F6",   # blue
    "table": "#EF4444",  # red
    "figure": "#22C55E",  # green
}


def main(pdf_path: str) -> None:
    pdf_path = Path(pdf_path)
    doc_id = pdf_path.stem
    pages_dir = Path("data/pages") / doc_id
    debug_dir = Path("data/debug_layout") / doc_id
    debug_dir.mkdir(parents=True, exist_ok=True)

    print(f"Rendering pages from {pdf_path} ...")
    pages = render_pdf(pdf_path, pages_dir)
    print(f"Rendered {len(pages)} pages -> {pages_dir}")

    print("Running layout detection (this can take a while on CPU) ...")
    regions = detect_layout(pdf_path)
    print(f"Detected {len(regions)} regions")

    by_page: dict[int, list] = {}
    for r in regions:
        by_page.setdefault(r.page_number, []).append(r)

    counts = {"text": 0, "table": 0, "figure": 0}
    for page in pages:
        img = Image.open(page.image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        for r in by_page.get(page.page_number, []):
            counts[r.region_type] += 1
            color = COLORS[r.region_type]
            draw.rectangle(r.bbox, outline=color, width=3)
            draw.text((r.bbox[0] + 2, r.bbox[1] + 2), r.region_type, fill=color)
        out_path = debug_dir / f"page_{page.page_number}.png"
        img.save(out_path)

    print(f"Region counts: {counts}")
    print(f"Annotated pages written to {debug_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/debug_layout.py <path-to-pdf>")
        sys.exit(1)
    main(sys.argv[1])
