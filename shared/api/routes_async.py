"""REST endpoints coordinating HTML and PPT generation."""

import hashlib
import os
import re
from base64 import b64decode
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from shared.logging import get_logger
from shared.api.generate_schema import GenerateQuery, IndicatorChart
from shared.auth import get_current_user
from shared.db.pg_metadata import get_ppt_metadata, save_ppt_metadata
from shared.api.task_manager import task_manager

logger = get_logger("routes_async")

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PPT_RESOURCES = PROJECT_ROOT / "ppt" / "resources"


@router.post("/generate")
async def generate_async(
    query: GenerateQuery,
    background_tasks: BackgroundTasks,
    user_properties: dict = Depends(get_current_user)
):
    user_name = user_properties.get("displayName")
    if not user_name:
        raise HTTPException(status_code=401, detail="Unauthorized")

    task_id = await task_manager.create_task()
    
    await save_ppt_metadata(
        user_id=query.userName,
        thread_id=query.threadId,
        task_id=task_id,
        status="accepted",
        is_processing=True
    )
    
    logger.info({
        "message": "Asynchronous generation task created",
        "task_id": task_id,
        "user_name": query.userName,
        "thread_id": query.threadId,
        "status": "created"
    })
    
    mode = os.getenv("MODE", "html").lower()
    
    background_tasks.add_task(
        process_generation_task,
        task_id=task_id,
        query=query,
        mode=mode
    )
    
    return JSONResponse({
        "taskId": task_id,
        "status": "accepted",
        "message": "Task accepted, processing..."
    }, status_code=202)


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    timeout: Optional[int] = Query(30, ge=0, le=60)
):
    import asyncio
    
    start_time = asyncio.get_event_loop().time()
    poll_interval = 0.5
    
    while True:
        task = await task_manager.get_task(task_id)
        
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} does not exist")
        
        if task.status in ["completed", "failed"]:
            return JSONResponse({
                "taskId": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "fileId": task.file_id,
                "error": task.error,
                "createdAt": task.created_at.isoformat(),
                "updatedAt": task.updated_at.isoformat()
            })
        
        elapsed = asyncio.get_event_loop().time() - start_time
        if timeout == 0 or elapsed >= timeout:
            return JSONResponse({
                "taskId": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "fileId": task.file_id,
                "error": task.error,
                "createdAt": task.created_at.isoformat(),
                "updatedAt": task.updated_at.isoformat()
            })
        
        await asyncio.sleep(poll_interval)


@router.get("/metadata")
async def get_metadata(
    userName: str = Query(...),
    threadId: str = Query(...),
    appId: Optional[str] = Query(None),
    user_properties: dict = Depends(get_current_user)
):
    user_name = user_properties.get("displayName")
    if not user_name:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        metadata = await get_ppt_metadata(userName, threadId, appId)
        
        if metadata is None:
            return JSONResponse({
                "threadId": threadId,
                "fileId": None,
                "taskId": None,
                "status": None,
                "isProcessing": False
            })
        
        return JSONResponse(metadata)
        
    except Exception as e:
        logger.error({
            "message": "Failed to get metadata",
            "user_name": userName,
            "thread_id": threadId,
            "error": str(e),
            "status": "error"
        })
        raise HTTPException(status_code=500, detail="Failed to retrieve metadata")


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    user_properties: dict = Depends(get_current_user)
):
    user_name = user_properties.get("displayName")
    if not user_name:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    file_path = None
    
    ppt_shared_dir = os.environ.get("PPTAUTO_SHARED_DIRECTORY")
    generated_files_dir = os.environ.get("GENERATED_FILES_DIR", "generated_files")
    
    search_dirs = []
    if ppt_shared_dir and os.path.exists(ppt_shared_dir):
        search_dirs.append(ppt_shared_dir)
    if os.path.exists(generated_files_dir):
        search_dirs.append(generated_files_dir)
    
    for base_dir in search_dirs:
        for user_hash_dir in os.listdir(base_dir):
            potential_path = os.path.join(base_dir, user_hash_dir, file_id)
            if os.path.isfile(potential_path):
                file_path = potential_path
                break
        if file_path:
            break
    
    if file_path is None or not os.path.exists(file_path):
        logger.error({
            "message": "File not found",
            "file_id": file_id,
            "status": "not_found"
        })
        raise HTTPException(status_code=404, detail="File not found")
    
    logger.info({
        "message": "File download request",
        "file_id": file_id,
        "file_path": file_path,
        "status": "success"
    })
    
    return FileResponse(
        path=file_path,
        filename=file_id,
        media_type="application/octet-stream"
    )


async def process_generation_task(task_id: str, query: GenerateQuery, mode: str):
    try:
        await task_manager.update_task(
            task_id,
            status="processing",
            progress=10,
            message="Start processing generation task"
        )
        
        if mode == "ppt":
            file_id = await generate_ppt_internal(task_id, query)
        elif mode == "html":
            file_id = await generate_html_internal(task_id, query)
        else:
            raise ValueError(f"Unsupported mode: {mode}")
        
        await task_manager.update_task(
            task_id,
            status="completed",
            progress=100,
            message="Generation completed",
            file_id=file_id
        )
        
        await save_ppt_metadata(
            user_id=query.userName,
            thread_id=query.threadId,
            file_id=file_id,
            task_id=task_id,
            status="completed",
            is_processing=False
        )
        
        logger.info({
            "message": "Task completed",
            "task_id": task_id,
            "file_id": file_id,
            "mode": mode,
            "status": "completed"
        })
        
    except Exception as e:
        logger.error({
            "message": "Task failed",
            "task_id": task_id,
            "error": str(e),
            "status": "failed"
        })
        
        await task_manager.update_task(
            task_id,
            status="failed",
            progress=0,
            message="Generation failed",
            error=str(e)
        )
        
        await save_ppt_metadata(
            user_id=query.userName,
            thread_id=query.threadId,
            task_id=task_id,
            status="failed",
            is_processing=False
        )


async def generate_ppt_internal(task_id: str, query: GenerateQuery) -> str:
    from ppt_generation.generator.pres_generator import ContentParser, PPTGenerator
    from ppt_generation.saver.pres_save import save_ppt_to_local
    
    await task_manager.update_task(task_id, progress=20, message="解析会话内容")
    
    # Extract chart information from assets or conversation
    assets = getattr(query, "assets", None)
    indicator_charts_in = getattr(assets, "indicatorCharts", None) if assets else None
    source_list = getattr(assets, "sourceList", None) if assets else None
    
    # If assets does not have, try to collect charts from conversation
    if not indicator_charts_in and query.conversation:
        charts_list = []
        for block in query.conversation:
            if "charts" in block and isinstance(block["charts"], list):
                charts_list.extend(block["charts"])
        if charts_list:
            indicator_charts_in = [IndicatorChart(**chart) for chart in charts_list]
    
    # If source_list does not have, try to collect sources from conversation
    if not source_list and query.conversation:
        sources_list = []
        for block in query.conversation:
            if "sources" in block and isinstance(block["sources"], list):
                sources_list.extend(block["sources"])
        if sources_list:
            source_list = sources_list
    
    await task_manager.update_task(task_id, progress=30, message="Decode chart data")
    decoded_charts = await decode_indicator_charts(indicator_charts_in)
    
    await task_manager.update_task(task_id, progress=40, message="Parse PPT content")
    ppt_content = ContentParser().parse(
        user_name=query.userName,
        conversation=query.conversation,
        decoded_charts=decoded_charts,
        source_list=source_list,
    )
    
    await task_manager.update_task(task_id, progress=60, message="Generate PPT file")
    ppt_generator = PPTGenerator(template_path=str(PPT_RESOURCES / "smbc_template_new.pptx"))
    ppt_file = ppt_generator.generate(ppt_content)
    
    await task_manager.update_task(task_id, progress=80, message="Save PPT file")
    
    # Generate file name
    first_question = ""
    if getattr(query, "conversation", None):
        first_question = (
            (query.conversation[0].get("question", {}) or {}).get("content", "")
        )
    thread_id = query.threadId
    ppt_filename = generate_filename(first_question, thread_id, "pptx")
    user_hash = generate_user_hash(query.userName)
    
    # Save file
    save_ppt_to_local(ppt_file, ppt_filename, user_hash)
    
    await task_manager.update_task(task_id, progress=90, message="PPT saved completed")
    
    return ppt_filename


async def generate_html_internal(task_id: str, query: GenerateQuery) -> str:
    from html_generation.generator.html_generator import HTMLContentParser, HTMLGenerator
    from html_generation.saver.html_save import save_html_to_local
    
    await task_manager.update_task(task_id, progress=30, message="Parse HTML content")
    
    html_content_parser = HTMLContentParser()
    content_data = html_content_parser.parse(
        user_name=query.userName,
        conversation=query.conversation,
    )
    
    await task_manager.update_task(task_id, progress=60, message="Generate HTML")
    html_generator = HTMLGenerator()
    html_content = html_generator.generate(content_data)
    
    await task_manager.update_task(task_id, progress=80, message="Save HTML file")
    
    # Generate file name
    first_question = ""
    if getattr(query, "conversation", None):
        first_question = query.conversation[0].get("question", {}).get("content", "")
    thread_id = query.threadId
    html_filename = generate_filename(first_question, thread_id, "html")
    user_hash = generate_user_hash(query.userName)
    
    # Save file
    save_html_to_local(html_content, html_filename, user_hash)
    
    await task_manager.update_task(task_id, progress=90, message="HTML saved completed")
    
    return html_filename


async def decode_indicator_charts(indicator_charts_data):
    decoded_charts = []
    if not indicator_charts_data:
        return decoded_charts

    try:
        for chart in indicator_charts_data:
            chart_dict = chart.dict()
            if "encodedImage" not in chart_dict:
                logger.warning({
                    "message": "Chart data is incomplete: 'encodedImage' is missing.",
                    "operation": "decode_charts",
                })
                continue

            decoded_chart = {"image": BytesIO(b64decode(chart_dict["encodedImage"]))}
            if "title" in chart_dict:
                decoded_chart["title"] = chart_dict["title"]
            if "label" in chart_dict:
                decoded_chart["label"] = chart_dict["label"]

            decoded_charts.append(decoded_chart)
        
    except Exception as e:
        logger.error({
            "message": "Error occurred during Base64 image decoding.",
            "operation": "decode_charts",
            "error_message": str(e),
            "status": "problem",
        })
        raise ValueError("Failed to decode image.")

    return decoded_charts


def generate_filename(user_question: str, thread_id: str, file_type: str = "pptx") -> str:
    current_date = datetime.now().strftime("%Y%m%d")
    sanitized_question = re.sub(r"[^\w\-_]", "_", user_question).rstrip("_")
    filename = f"{current_date}-{sanitized_question}-{thread_id}.{file_type}"
    return filename


def generate_user_hash(user_name: str) -> str:
    user_hash = hashlib.md5(user_name.encode("utf-8")).hexdigest()
    return user_hash
