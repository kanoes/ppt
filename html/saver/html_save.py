"""Helpers for persisting generated HTML artifacts."""

import os
from pathlib import Path

from shared.config import settings
from shared.logging import get_logger

logger = get_logger("html_save")

BASE_HTML_DIR = Path(settings.generated_files_dir)


def save_html_to_local(html_content: str, html_filename: str, user_hash: str) -> Path:
    """Persist HTML output to the local filesystem."""
    try:
        user_dir = BASE_HTML_DIR / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)

        html_file_path = user_dir / html_filename

        html_file_path.write_text(html_content, encoding="utf-8")

        logger.info({
            "message": "HTML document saved",
            "operation": "html_save",
            "file_path": str(html_file_path),
            "user_hash": user_hash,
            "status": "completed"
        })

        return Path(html_filename)

    except Exception as e:
        logger.error({
            "message": "Failed to save HTML document",
            "operation": "html_save",
            "error_message": str(e),
            "user_hash": user_hash,
            "filename": html_filename,
            "status": "problem"
        })
        raise


def get_html_file_path(html_filename: str, user_hash: str) -> Path:
    """Return the resolved path for a stored HTML file."""
    user_dir = BASE_HTML_DIR / user_hash
    return user_dir / html_filename


def html_file_exists(html_filename: str, user_hash: str) -> bool:
    """Check whether a generated HTML file already exists."""
    html_file_path = get_html_file_path(html_filename, user_hash)
    return html_file_path.exists()


def read_html_file(html_filename: str, user_hash: str) -> str:
    """Load the stored HTML content for a user."""
    try:
        html_file_path = get_html_file_path(html_filename, user_hash)

        if not html_file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")

        content = html_file_path.read_text(encoding="utf-8")

        logger.info({
            "message": "HTML document loaded",
            "operation": "html_read",
            "file_path": str(html_file_path),
            "user_hash": user_hash,
            "status": "completed"
        })
        
        return content
        
    except Exception as e:
        logger.error({
            "message": "Failed to read HTML document",
            "operation": "html_read",
            "error_message": str(e),
            "user_hash": user_hash,
            "filename": html_filename,
            "status": "problem"
        })
        raise
