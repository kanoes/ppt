import os
from pathlib import Path
from typing import BinaryIO

from src.logging import get_logger

# ログ設定
logger = get_logger("html_save")


def save_html_to_local(html_content: str, html_filename: str, user_hash: str) -> None:
    """
    HTML文書をローカルファイルシステムに保存する
    """
    try:
        # ユーザーディレクトリのパスを作成
        user_dir = Path(f"generated_files/{user_hash}")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # HTMLファイルのパスを作成
        html_file_path = user_dir / html_filename
        
        # HTMLファイルを保存
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info({
            "message": "HTML文書の保存が完了しました。",
            "operation": "html_save",
            "file_path": str(html_file_path),
            "user_hash": user_hash,
            "status": "completed"
        })
        
    except Exception as e:
        logger.error({
            "message": "HTML文書の保存中にエラーが発生しました。",
            "operation": "html_save",
            "error_message": str(e),
            "user_hash": user_hash,
            "filename": html_filename,
            "status": "problem"
        })
        raise


def get_html_file_path(html_filename: str, user_hash: str) -> Path:
    """
    HTMLファイルのパスを取得する
    """
    user_dir = Path(f"generated_files/{user_hash}")
    return user_dir / html_filename


def html_file_exists(html_filename: str, user_hash: str) -> bool:
    """
    HTMLファイルが存在するかチェックする
    """
    html_file_path = get_html_file_path(html_filename, user_hash)
    return html_file_path.exists()


def read_html_file(html_filename: str, user_hash: str) -> str:
    """
    HTMLファイルを読み込む
    """
    try:
        html_file_path = get_html_file_path(html_filename, user_hash)
        
        if not html_file_path.exists():
            raise FileNotFoundError(f"HTMLファイルが見つかりません: {html_file_path}")
        
        with open(html_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info({
            "message": "HTMLファイルの読み込みが完了しました。",
            "operation": "html_read",
            "file_path": str(html_file_path),
            "user_hash": user_hash,
            "status": "completed"
        })
        
        return content
        
    except Exception as e:
        logger.error({
            "message": "HTMLファイルの読み込み中にエラーが発生しました。",
            "operation": "html_read",
            "error_message": str(e),
            "user_hash": user_hash,
            "filename": html_filename,
            "status": "problem"
        })
        raise 