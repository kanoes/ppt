"""Persistence helpers for generated PPT files."""

from pathlib import Path
from io import BytesIO

from shared.config import settings
from shared.logging import get_logger

logger = get_logger("pres_save")


def save_ppt_to_local(file_stream: BytesIO, file_name: str, user_hash: str) -> Path:
    """Persist a PPT stream to the shared directory and return the stored path."""

    base_path = Path(settings.ppt_shared_directory or ".").resolve()
    relative_path = Path(user_hash) / file_name
    full_file_path = base_path / relative_path

    logger.info({
        "message": "Saving PowerPoint document",
        "operation": "save_ppt_to_local",
        "file_name": file_name,
        "target_path": str(full_file_path),
        "status": "started",
    })

    try:
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        with full_file_path.open("wb") as out_file:
            out_file.write(file_stream.getbuffer())

        logger.info({
            "message": "PowerPoint document saved",
            "operation": "save_ppt_to_local",
            "file_name": file_name,
            "target_path": str(full_file_path),
            "status": "completed",
        })
        return relative_path
    except Exception as e:
        logger.error({
            "message": "Failed to save PowerPoint document",
            "operation": "save_ppt_to_local",
            "file_name": file_name,
            "target_path": str(full_file_path),
            "error_message": str(e),
            "status": "problem",
        })
        raise
