from pathlib import Path

from config import get_settings


class FileStore:
    """Simple local file storage for page/crop images."""

    def __init__(self):
        self.settings = get_settings()

    def save_page(self, doc_id: str, page_number: int, image_bytes: bytes) -> str:
        """Save a page image and return its path."""
        page_dir = self.settings.pages_dir / doc_id
        page_dir.mkdir(parents=True, exist_ok=True)
        path = page_dir / f"page_{page_number}.png"
        path.write_bytes(image_bytes)
        return str(path)

    def save_crop(self, doc_id: str, chunk_id: str, image_bytes: bytes) -> str:
        """Save a cropped region image and return its path."""
        crop_dir = self.settings.crops_dir / doc_id
        crop_dir.mkdir(parents=True, exist_ok=True)
        path = crop_dir / f"{chunk_id}.png"
        path.write_bytes(image_bytes)
        return str(path)

    def load_page(self, doc_id: str, page_number: int) -> bytes | None:
        """Load a page image."""
        path = self.settings.pages_dir / doc_id / f"page_{page_number}.png"
        return path.read_bytes() if path.exists() else None

    def load_crop(self, doc_id: str, chunk_id: str) -> bytes | None:
        """Load a cropped region image."""
        path = self.settings.crops_dir / doc_id / f"{chunk_id}.png"
        return path.read_bytes() if path.exists() else None
