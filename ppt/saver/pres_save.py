"""Persistence helpers for generated PPT files."""

import os
from io import BytesIO

from shared.logging import get_logger

logger = get_logger("pres_save")


def save_ppt_to_local(file_stream: BytesIO, file_name: str, user_hash: str) -> str:
    """
    PowerPointファイルをローカルディレクトリに保存する関数。
    """
    logger.info({
        "message": "パワポの保存を開始します。",
        "file_name": file_name,
        "operation": "save_ppt_to_local",
        "status": "start"
    })

    # 保存先のベースパスを取得
    try:
        base_path = os.getenv("PPTAUTO_SHARED_DIRECTORY", "./")
        
    except Exception as e:
        logger.error({
            "message": "環境変数 'PPTAUTO_SHARED_DIRECTORY' が設定されていません。",
            "operation": "save_ppt_to_local",
            "status": "problem"
        })
        raise

    # 保存先の完全なパスを生成
    file_path = os.path.join(user_hash, file_name)
    full_file_path = os.path.join(base_path, file_path)

    # 必要に応じてディレクトリを作成
    try:
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
    except Exception as e:
        logger.error({
            "message": "ディレクトリの作成に失敗しました。",
            "operation": "save_ppt_to_local",
            "status": "problem"
        })
        raise

    # ファイルを保存
    try:
        with open(full_file_path, "wb") as out_file:
            out_file.write(file_stream.getbuffer())
        logger.info({"message": "パワポの保存が完了しました。",},
                    {"operation": "save_ppt_to_local",
                    "status": "completed"})
        
    except Exception as e:
        logger.error({
                "message": "ファイルの保存に失敗しました。",
                "operation": "save_ppt_to_local",
                "status": "problem"
            })
        raise

    return full_file_path
