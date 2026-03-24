import uuid
from datetime import UTC, datetime
from pathlib import Path

from mahmoney.config import get_settings


async def save_file(content: bytes, original_filename: str) -> Path:
    settings = get_settings()
    now = datetime.now(tz=UTC)

    # Organize by year/month
    directory = settings.storage_path / str(now.year) / f"{now.month:02d}"
    directory.mkdir(parents=True, exist_ok=True)

    # Preserve extension, use UUID for uniqueness
    ext = Path(original_filename).suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = directory / filename

    file_path.write_bytes(content)

    # Return path relative to storage root
    return file_path.relative_to(settings.storage_path)
