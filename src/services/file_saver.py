import os
from pathlib import Path
from typing import BinaryIO

from src.logging import get_logger

logger = get_logger("file_saver")


def save_file_to_local(file_io: BinaryIO, filename: str, user_hash: str):
    """
    Save file to local storage organized by user hash
    
    Args:
        file_io: Binary file content
        filename: Name of the file
        user_hash: MD5 hash of username for directory organization
    """
    try:
        output_dir = Path("output") / user_hash
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        with open(output_path, "wb") as f:
            f.write(file_io.read())
        
        logger.info({
            "message": "File saved successfully",
            "operation": "file_save",
            "filename": filename,
            "path": str(output_path),
            "status": "completed",
        })
        
    except Exception as e:
        logger.error({
            "message": "Error saving file",
            "operation": "file_save",
            "filename": filename,
            "error_message": str(e),
            "status": "failed",
        })
        raise

