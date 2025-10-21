from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Sequence

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.api.generate_schema import GenerateQuery
from src.logging import get_logger
from src.services.html_saver.html_save import save_html_to_local
from src.services.presentation_pipeline import PresentationArtifacts, PresentationPipeline
from src.services.ppt_saver.pres_save import save_ppt_to_local

logger = get_logger("routes_generate")
router = APIRouter()
_pipeline = PresentationPipeline()


@router.post("/generate")
async def generate_presentation(query: GenerateQuery):
    logger.info(
        {
            "message": "プレゼンテーション生成リクエストを受信しました。",
            "user_name": query.userName,
            "status": "received",
        }
    )

    assets_dict: Dict[str, Any] = {}
    if getattr(query, "assets", None):
        try:
            assets_dict = query.assets.model_dump()  # type: ignore[assignment]
        except AttributeError:
            assets_dict = query.assets or {}

    try:
        artifacts: PresentationArtifacts = _pipeline.build(
            user_name=query.userName,
            conversation=query.conversation,
            assets=assets_dict,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            {
                "message": "プレゼンテーションの生成に失敗しました。",
                "user_name": query.userName,
                "status": "problem",
                "error_message": str(exc),
            }
        )
        return JSONResponse({"error": "プレゼンテーションの生成に失敗しました。"}, status_code=500)

    first_question = _extract_first_question(query.conversation)
    user_hash = generate_user_hash(query.userName)
    ppt_filename = generate_filename(first_question, query.threadId, "pptx")
    html_filename = generate_filename(first_question, query.threadId, "html")

    try:
        save_html_to_local(artifacts.html, html_filename, user_hash)
        save_ppt_to_local(artifacts.ppt_stream, ppt_filename, user_hash)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            {
                "message": "生成ファイルの保存に失敗しました。",
                "user_name": query.userName,
                "status": "problem",
                "error_message": str(exc),
            }
        )
        return JSONResponse({"error": "生成ファイルの保存に失敗しました。"}, status_code=500)

    logger.info(
        {
            "message": "プレゼンテーションの生成と保存が完了しました。",
            "user_name": query.userName,
            "ppt_filename": ppt_filename,
            "html_filename": html_filename,
            "status": "success",
        }
    )

    return JSONResponse(
        {
            "pptFileId": ppt_filename,
            "htmlFileId": html_filename,
            "userHash": user_hash,
        },
        status_code=200,
    )


def generate_filename(user_question: str, thread_id: str, file_type: str = "pptx") -> str:
    current_date = datetime.now().strftime("%Y%m%d")
    sanitized_question = re.sub(r"[^\w\-_]", "_", user_question).rstrip("_")
    filename = f"{current_date}-{sanitized_question}-{thread_id}.{file_type}"
    return filename


def generate_user_hash(user_name: str) -> str:
    return hashlib.md5(user_name.encode("utf-8")).hexdigest()


def _extract_first_question(conversation: Sequence[Dict[str, Any]]) -> str:
    if not conversation:
        return "presentation"
    first = conversation[0] or {}
    question = (first.get("question") or {}).get("content") if isinstance(first, dict) else None
    return (question or "presentation").strip() or "presentation"

