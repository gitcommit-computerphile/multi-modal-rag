from pathlib import Path

from PIL import Image

from models.factory import get_vision_client


def caption_table_region(image_path: Path, bbox: tuple) -> str:
    """Crop a table region from a page image and get VLM description."""
    img = Image.open(image_path).convert("RGB")
    x0, y0, x1, y1 = [int(v) for v in bbox]
    cropped = img.crop((x0, y0, x1, y1))

    # Convert to bytes
    img_bytes = cropped.tobytes("png")

    client = get_vision_client()
    return client.describe_table(img_bytes)


def caption_figure_region(image_path: Path, bbox: tuple, nearby_text: str = "") -> str:
    """Crop a figure region from a page image and get VLM description."""
    img = Image.open(image_path).convert("RGB")
    x0, y0, x1, y1 = [int(v) for v in bbox]
    cropped = img.crop((x0, y0, x1, y1))

    # Convert to bytes
    img_bytes = cropped.tobytes("png")

    client = get_vision_client()
    return client.describe_figure(img_bytes, context=nearby_text)
