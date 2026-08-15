import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw

from db.models import Chunk
from db.session import get_session
from storage.file_store import FileStore

router = APIRouter(prefix="/chunks", tags=["chunks"])

HIGHLIGHT_COLORS = {
    "text": "#3B82F6",
    "table": "#EF4444",
    "figure": "#22C55E",
}


@router.get("/{chunk_id}/preview")
def get_chunk_preview(chunk_id: str, crop: bool = False):
    """Serve the source page image with this chunk's region outlined.

    bbox is in the same RENDER_DPI pixel space as the stored page image, so it
    can be drawn directly without conversion. With crop=true, returns just the
    region (padded) instead of the full page.
    """
    session = get_session()
    chunk = session.query(Chunk).filter(Chunk.id == chunk_id).first()
    session.close()

    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    page_bytes = FileStore().load_page(chunk.document_id, chunk.page_number)
    if page_bytes is None:
        raise HTTPException(status_code=404, detail="Page image not found")

    image = Image.open(io.BytesIO(page_bytes)).convert("RGB")

    if chunk.bbox:
        x0, y0, x1, y1 = (float(v) for v in chunk.bbox)
        color = HIGHLIGHT_COLORS.get(chunk.source_type, "#3B82F6")

        if crop:
            pad = 24
            box = (
                max(0, int(x0) - pad),
                max(0, int(y0) - pad),
                min(image.width, int(x1) + pad),
                min(image.height, int(y1) + pad),
            )
            image = image.crop(box)
        else:
            draw = ImageDraw.Draw(image, "RGBA")
            draw.rectangle([x0, y0, x1, y1], outline=color, width=6)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
