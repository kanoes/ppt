from __future__ import annotations

from pathlib import Path

from src.logging import get_logger

logger = get_logger("html_save")


def save_html_to_local(html_content: str, html_filename: str, user_hash: str) -> None:
    """Persist generated HTML content to disk."""
    try:
        user_dir = Path("generated_files") / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)

        html_file_path = user_dir / html_filename
        html_file_path.write_text(html_content, encoding="utf-8")

        logger.info(
            {
                "message": "HTML文書の保存が完了しました。",
                "operation": "html_save",
                "file_path": str(html_file_path),
                "user_hash": user_hash,
                "status": "completed",
            }
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            {
                "message": "HTML文書の保存中にエラーが発生しました。",
                "operation": "html_save",
                "error_message": str(exc),
                "user_hash": user_hash,
                "filename": html_filename,
                "status": "problem",
            }
        )
        raise


def get_html_file_path(html_filename: str, user_hash: str) -> Path:
    return Path("generated_files") / user_hash / html_filename


def html_file_exists(html_filename: str, user_hash: str) -> bool:
    return get_html_file_path(html_filename, user_hash).exists()


def read_html_file(html_filename: str, user_hash: str) -> str:
    try:
        html_file_path = get_html_file_path(html_filename, user_hash)
        if not html_file_path.exists():
            raise FileNotFoundError(f"HTMLファイルが見つかりません: {html_file_path}")

        content = html_file_path.read_text(encoding="utf-8")
        logger.info(
            {
                "message": "HTMLファイルの読み込みが完了しました。",
                "operation": "html_read",
                "file_path": str(html_file_path),
                "user_hash": user_hash,
                "status": "completed",
            }
        )
        return content
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            {
                "message": "HTMLファイルの読み込み中にエラーが発生しました。",
                "operation": "html_read",
                "error_message": str(exc),
                "user_hash": user_hash,
                "filename": html_filename,
                "status": "problem",
            }
        )
        raise

