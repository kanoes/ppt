import hashlib
import re
import os
from typing import Literal

from datetime import datetime
from base64 import b64decode
from io import BytesIO
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.logging import get_logger
from src.api.generate_schema import GenerateQuery

# ログ設定
logger = get_logger("routes_generate")

# FastAPIのルーター
router = APIRouter()


@router.post("/generate-ppt")
async def generate_ppt(query: GenerateQuery):
    """
    パワポを生成し保存するエンドポイント。
    """
    from src.services.ppt_saver.pres_save import save_ppt_to_local
    from src.services.ppt_generator.pres_generator import ContentParser, PPTGenerator

    logger.info(
        {
            "message": "パワポ生成リクエストを受信しました。",
            "user_name": query.userName,
            "mode": "ppt",
            "status": "received",
        }
    )

    assets = getattr(query, "assets", None)
    indicator_charts_in = getattr(assets, "indicatorCharts", None) if assets else None
    source_list = getattr(assets, "sourceList", None) if assets else None

    decoded_charts = await decode_indicator_charts(indicator_charts_in)

    max_retries = 2
    ppt_file = None
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            # conversation からタイトル/本文をまとめるのは ContentParser 側で実施
            ppt_content = ContentParser().parse(
                user_name=query.userName,
                conversation=query.conversation,
                decoded_charts=decoded_charts,
                source_list=source_list,  # ← 新：引用元も渡す
            )

            ppt_generator = PPTGenerator(template_path="resources/smbc_template_new.pptx")
            ppt_file = ppt_generator.generate(ppt_content)
            break  # 成功

        except Exception as e:
            last_err = e
            if attempt < max_retries:
                logger.warning(
                    {
                        "message": "PPTの生成に失敗しました。再試行します。",
                        "user_name": query.userName,
                        "attempt": attempt + 1,
                        "status": "retrying",
                        "error_message": str(e),
                    }
                )
            else:
                logger.error(
                    {
                        "message": "PPTの生成に失敗し、最大再試行回数に達しました。",
                        "user_name": query.userName,
                        "status": "problem",
                        "error_message": str(e),
                    }
                )

    if ppt_file is None:
        return JSONResponse({"error": "パワポの生成は失敗しました。"}, status_code=500)

    # ------------- ファイル名の生成 -------------
    first_question = (
        (query.conversation[0].get("question", {}) or {}).get("content", "")
        if getattr(query, "conversation", None)
        else ""
    )
    thread_id = query.threadId
    ppt_filename = generate_filename(first_question, thread_id, "pptx")
    user_hash = generate_user_hash(query.userName)

    # ------------- ローカル保存 -------------
    try:
        save_ppt_to_local(ppt_file, ppt_filename, user_hash)
        logger.info(
            {
                "message": "パワポの生成と保存は成功しました。",
                "user_name": query.userName,
                "file_name": ppt_filename,
                "status": "success",
            }
        )
        return JSONResponse({"fileId": ppt_filename}, 200)

    except Exception as e:
        logger.error(
            {
                "message": "パワポの保存にエラーが発生しました。",
                "user_name": query.userName,
                "status": "failed",
                "error_message": str(e),
            }
        )
        return JSONResponse({"error": "PPTファイルの保存は失敗しました。"}, status_code=500)



@router.post("/generate-html")
async def generate_html(query: GenerateQuery):
    """
    HTMLを生成し保存するエンドポイント。
    """
    from src.services.html_generator.html_generator import HTMLContentParser, HTMLGenerator
    from src.services.html_saver.html_save import save_html_to_local
    logger.info(
        {
            "message": "HTML生成リクエストを受信しました。",
            "user_name": query.userName,
            "mode": "html",
            "status": "received",
        }
    )

    user_hash = generate_user_hash(query.userName)

    try:
        # HTMLコンテンツの解析
        html_content_parser = HTMLContentParser()
        content_data = html_content_parser.parse(
            user_name=query.userName,
            conversation=query.conversation,
        )

        # HTMLの生成
        html_generator = HTMLGenerator()
        html_content = html_generator.generate(content_data)

        # ファイル名の生成
        first_question = query.conversation[0].get("question", {}).get("content", "")
        thread_id = query.threadId
        html_filename = generate_filename(first_question, thread_id, "html")

        # HTMLファイルをローカルに保存
        save_html_to_local(html_content, html_filename, user_hash)

        logger.info(
            {
                "message": "HTMLの生成と保存は成功しました。",
                "user_name": query.userName,
                "file_name": html_filename,
                "status": "success",
            }
        )

        # 成功レスポンスを返す
        return JSONResponse({"fileId": html_filename, "mode": "html"}, 200)

    except Exception as e:
        logger.error(
            {
                "message": "HTMLの生成にエラーが発生しました。",
                "user_name": query.userName,
                "status": "failed",
                "error_message": str(e),
            }
        )

        return JSONResponse(
            {"error": "HTMLファイルの生成は失敗しました。"}, status_code=500
        )


async def decode_indicator_charts(indicator_charts_data):
    """
    チャート情報をデコードする。
    """
    logger.info(
            {
                "message": "チャートのデコードを開始します。",
                "operation": "decode_charts",
                "status": "started",
            }
        )
    
    decoded_charts = []
    if not indicator_charts_data:
        logger.info({"message": "デコードできるチャートがありません。",
                     "operation": "decode_charts",
                     "status": "completed"})
        return decoded_charts

    try:
        for chart in indicator_charts_data:
            chart_dict = chart.dict()
            if "encodedImage" not in chart_dict:
                logger.warning(
                    {
                        "message": "チャートのデータが不完全です: 'encodedImage' が欠けています。",
                        "operation": "decode_charts",
                    }
                )
                continue

            # デコードされたチャート情報を保存
            decoded_chart = {"image": BytesIO(b64decode(chart_dict["encodedImage"]))}
            # title と label はオプショナルとして含める
            if "title" in chart_dict:
                decoded_chart["title"] = chart_dict["title"]
            if "label" in chart_dict:
                decoded_chart["label"] = chart_dict["label"]

            decoded_charts.append(decoded_chart)

        logger.info(
            {"message": f"{len(decoded_charts)} 枚のチャートのデコードが成功しました。",
             "operation": "decode_charts",
             "status": "completed"}
        )
        
    except Exception as e:
        logger.error(
            {
                "message": "Base64画像デコード中にエラーが発生しました。",
                "operation": "decode_charts",
                "error_message": str(e),
                "status": "problem",
            }
        )
        raise ValueError("画像デコードに失敗しました。")

    return decoded_charts


async def generate_presentation_file(query: GenerateQuery, decoded_charts):
    """
    パワポファイルを生成する。
    """
    max_retries = 2  # 最大試行回数

    for attempt in range(max_retries + 1):
        try:
            ppt_content = ContentParser().parse(
                user_name=query.userName,
                conversation=query.conversation,
                decoded_charts=decoded_charts,
            )

            ppt_generator = PPTGenerator(
                template_path="resources/smbc_template_new.pptx"
            )
            ppt_file = ppt_generator.generate(ppt_content)

            return ppt_file

        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    {
                        "message": "PPTの生成に失敗しました。再試行中。",
                        "user_name": query.userName,
                        "attempt": attempt + 1,
                        "status": "retrying",
                        "error_message": str(e),
                    }
                )
            else:
                logger.error(
                    {
                        "message": "PPTの生成に失敗し、最大再試行回数に達しました。",
                        "user_name": query.userName,
                        "status": "problem",
                        "error_message": str(e),
                    }
                )
                return None


def generate_filename(user_question: str, thread_id: str, file_type: str = "pptx") -> str:
    """
    ファイル名を生成する。
    """
    current_date = datetime.now().strftime("%Y%m%d")
    sanitized_question = re.sub(r"[^\w\-_]", "_", user_question).rstrip("_")
    filename = f"{current_date}-{sanitized_question}-{thread_id}.{file_type}"
    return filename


def generate_user_hash(user_name: str) -> str:
    """
    ユーザー名のハッシュ値を生成する。
    """
    user_hash = hashlib.md5(user_name.encode("utf-8")).hexdigest()
    return user_hash


# =========================================================
# 起動MODE
# =========================================================
MODE: Literal["ppt", "html"] = os.getenv("MODE", "html").lower()  # type: ignore[assignment]

if MODE == "ppt":
    router.add_api_route(
        "/generate",
        generate_ppt,
        methods=["POST"],
        name="generate (ppt)",
        tags=["generate"],
    )
elif MODE == "html":
    router.add_api_route(
        "/generate",
        generate_html,
        methods=["POST"],
        name="generate (html)",
        tags=["generate"],
    )
else:
    raise RuntimeError(f"Invalid MODE={MODE!r}. Use 'ppt' or 'html'.")