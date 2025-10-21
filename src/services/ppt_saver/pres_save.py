from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

from src.logging import get_logger

logger = get_logger("pres_save")


def save_ppt_to_local(file_stream: BytesIO, file_name: str, user_hash: str) -> str:
    """Save a generated PowerPoint file to the shared directory."""
    base_path = Path(os.getenv("PPTAUTO_SHARED_DIRECTORY", "."))
    target_dir = base_path / user_hash
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / file_name

    logger.info(
        {
            "message": "パワポの保存を開始します。",
            "operation": "save_ppt_to_local",
            "file_name": file_name,
            "status": "started",
        }
    )

    try:
        with destination.open("wb") as out_file:
            out_file.write(file_stream.getbuffer())
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            {
                "message": "ファイルの保存に失敗しました。",
                "operation": "save_ppt_to_local",
                "file_name": file_name,
                "status": "problem",
                "error_message": str(exc),
            }
        )
        raise

    logger.info(
        {
            "message": "パワポの保存が完了しました。",
            "operation": "save_ppt_to_local",
            "file_path": str(destination),
            "status": "completed",
        }
    )

    return str(destination)

