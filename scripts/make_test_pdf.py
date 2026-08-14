"""Create a synthetic financial-report PDF with a real bordered table and a
rendered bar chart, so layout detection has actual Table/Image regions to find."""
import io
import sys
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PAGE_WIDTH, PAGE_HEIGHT = 612, 792  # US Letter, points

doc = fitz.open()

# --- Page 1: title, intro text, bordered table ---
page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

y = 50
page.insert_text((50, y), "Acme Corp - Q3 2024 Financial Summary", fontsize=18)

y += 35
intro = (
    "Acme Corp reported strong results for the third quarter of 2024, with revenue "
    "growth accelerating across all regions. The following table summarizes revenue "
    "and year-over-year growth by region."
)
page.insert_textbox(fitz.Rect(50, y, PAGE_WIDTH - 50, y + 60), intro, fontsize=11)

y += 80
page.insert_text((50, y), "Revenue by Region", fontsize=13)

# Bordered table
y += 20
table_data = [
    ["Region", "Revenue ($M)", "YoY Growth"],
    ["North America", "45.2", "12%"],
    ["Europe", "28.5", "8%"],
    ["Asia-Pacific", "38.9", "22%"],
    ["Total", "112.6", "14%"],
]
col_widths = [180, 150, 150]
row_height = 26
table_left = 50
table_top = y

n_rows = len(table_data)
table_width = sum(col_widths)
table_height = row_height * n_rows

# Outer border + row/column lines
for r in range(n_rows + 1):
    y_line = table_top + r * row_height
    page.draw_line((table_left, y_line), (table_left + table_width, y_line))
x_pos = table_left
for c_width in [0] + col_widths:
    x_pos += c_width
    page.draw_line((x_pos, table_top), (x_pos, table_top + table_height))

for row_idx, row in enumerate(table_data):
    cell_y = table_top + row_idx * row_height + row_height * 0.65
    x = table_left
    for col_idx, cell in enumerate(row):
        fontsize = 10 if row_idx > 0 else 10
        page.insert_text((x + 8, cell_y), cell, fontsize=fontsize)
        x += col_widths[col_idx]

y = table_top + table_height + 40
note = (
    "Net income increased 15% year-over-year to $25.1M, driven by operational "
    "efficiency gains and continued expansion in the Asia-Pacific market."
)
page.insert_textbox(fitz.Rect(50, y, PAGE_WIDTH - 50, y + 60), note, fontsize=11)

# --- Page 2: bar chart image + commentary text ---
page2 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

y = 50
page2.insert_text((50, y), "Revenue by Region - Chart", fontsize=16)

fig, ax = plt.subplots(figsize=(5, 3.2), dpi=150)
regions = ["North America", "Europe", "Asia-Pacific"]
revenue = [45.2, 28.5, 38.9]
ax.bar(regions, revenue, color=["#3B82F6", "#EF4444", "#22C55E"])
ax.set_ylabel("Revenue ($M)")
ax.set_title("Q3 2024 Revenue by Region")
for i, v in enumerate(revenue):
    ax.text(i, v + 1, str(v), ha="center", fontsize=9)
fig.tight_layout()

buf = io.BytesIO()
fig.savefig(buf, format="png")
plt.close(fig)
buf.seek(0)
chart_bytes = buf.read()

y += 20
chart_rect = fitz.Rect(60, y, 60 + 400, y + 260)
page2.insert_image(chart_rect, stream=chart_bytes)

y = chart_rect.y1 + 30
commentary = (
    "Asia-Pacific was the fastest-growing region in Q3 2024, with revenue up 22% "
    "year-over-year, outpacing North America (12%) and Europe (8%). Management "
    "attributes this to new product launches in the region and favorable currency "
    "movements."
)
page2.insert_textbox(fitz.Rect(50, y, PAGE_WIDTH - 50, y + 80), commentary, fontsize=11)

output_path = Path("samples") / "test_financial.pdf"
output_path.parent.mkdir(exist_ok=True)
doc.save(output_path)
print(f"Test PDF created: {output_path} ({len(doc)} pages)")