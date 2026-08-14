"""Test M1: pdf rendering + text extraction."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.pdf_loader import render_pdf

pdf_path = Path("samples/test_financial.pdf")
output_dir = Path("data/pages/test_doc")

print(f"Testing M1 on {pdf_path}...")
pages = render_pdf(pdf_path, output_dir)

print(f"\nRendered {len(pages)} pages:")
for page in pages:
    print(f"  Page {page.page_number}: {page.width}x{page.height}, {len(page.text_blocks)} text blocks")
    for block in page.text_blocks:
        print(f"    - {block.text[:60]}")

print(f"\nPages saved to {output_dir}")
print("✅ M1 rendering test passed")
