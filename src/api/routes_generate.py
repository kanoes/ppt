import hashlib
import re
from datetime import datetime
from base64 import b64decode
from io import BytesIO
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.logging import get_logger
from src.api.generate_schema import GenerateQuery
from src.workflows.presentation_workflow import PresentationWorkflow

logger = get_logger("routes_generate")

router = APIRouter()


@router.post("/generate")
async def generate_presentation(query: GenerateQuery):
    """
    Unified endpoint for presentation generation
    HTML generation → PPTX conversion workflow
    """
    logger.info({
        "message": "Received presentation generation request",
        "user_name": query.userName,
        "status": "received",
    })

    try:
        assets = getattr(query, "assets", None)
        indicator_charts = getattr(assets, "indicatorCharts", None) if assets else None
        source_list = getattr(assets, "sourceList", None) if assets else None

        decoded_charts = await decode_charts(indicator_charts)

        workflow = PresentationWorkflow()
        
        max_retries = 2
        ppt_file = None
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                ppt_file = workflow.generate_presentation(
                    user_name=query.userName,
                    conversation=query.conversation,
                    decoded_charts=decoded_charts,
                    source_list=source_list,
                )
                break

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning({
                        "message": "Presentation generation failed, retrying",
                        "user_name": query.userName,
                        "attempt": attempt + 1,
                        "status": "retrying",
                        "error_message": str(e),
                    })
                else:
                    logger.error({
                        "message": "Presentation generation failed after max retries",
                        "user_name": query.userName,
                        "status": "failed",
                        "error_message": str(e),
                    })

        if ppt_file is None:
            return JSONResponse(
                {"error": "Presentation generation failed"},
                status_code=500
            )

        first_question = (
            (query.conversation[0].get("question", {}) or {}).get("content", "")
            if getattr(query, "conversation", None)
            else ""
        )
        thread_id = query.threadId
        filename = generate_filename(first_question, thread_id, "pptx")
        user_hash = generate_user_hash(query.userName)

        from src.services.file_saver import save_file_to_local
        save_file_to_local(ppt_file, filename, user_hash)

        logger.info({
            "message": "Presentation generation and save completed successfully",
            "user_name": query.userName,
            "file_name": filename,
            "status": "success",
        })

        return JSONResponse({"fileId": filename}, 200)

    except Exception as e:
        logger.error({
            "message": "Error in presentation generation",
            "user_name": query.userName,
            "status": "failed",
            "error_message": str(e),
        })
        return JSONResponse(
            {"error": "Presentation generation failed"},
            status_code=500
        )


async def decode_charts(indicator_charts_data):
    """Decode chart images from base64"""
    logger.info({
        "message": "Starting chart decoding",
        "operation": "decode_charts",
        "status": "started",
    })
    
    decoded_charts = []
    if not indicator_charts_data:
        logger.info({
            "message": "No charts to decode",
            "operation": "decode_charts",
            "status": "completed"
        })
        return decoded_charts

    try:
        for chart in indicator_charts_data:
            chart_dict = chart.dict()
            if "encodedImage" not in chart_dict:
                logger.warning({
                    "message": "Chart missing encodedImage field",
                    "operation": "decode_charts",
                })
                continue

            decoded_chart = {
                "image": BytesIO(b64decode(chart_dict["encodedImage"]))
            }
            
            if "title" in chart_dict:
                decoded_chart["title"] = chart_dict["title"]
            if "label" in chart_dict:
                decoded_chart["label"] = chart_dict["label"]

            decoded_charts.append(decoded_chart)

        logger.info({
            "message": f"Decoded {len(decoded_charts)} chart(s) successfully",
            "operation": "decode_charts",
            "status": "completed"
        })
        
    except Exception as e:
        logger.error({
            "message": "Error decoding charts",
            "operation": "decode_charts",
            "error_message": str(e),
            "status": "failed",
        })
        raise ValueError("Chart decoding failed")

    return decoded_charts


def generate_filename(user_question: str, thread_id: str, file_type: str = "pptx") -> str:
    """Generate filename from question and thread ID"""
    current_date = datetime.now().strftime("%Y%m%d")
    sanitized_question = re.sub(r"[^\w\-_]", "_", user_question).rstrip("_")
    filename = f"{current_date}-{sanitized_question}-{thread_id}.{file_type}"
    return filename


def generate_user_hash(user_name: str) -> str:
    """Generate MD5 hash of username"""
    user_hash = hashlib.md5(user_name.encode("utf-8")).hexdigest()
    return user_hash
