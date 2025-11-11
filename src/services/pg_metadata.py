import os
from typing import Optional, Dict, Any

from src.services.db import get_pg_pool
from src.logging import get_logger

logger = get_logger("pg_metadata")


async def get_ppt_metadata(user_id: str, thread_id: str, app_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    pool = await get_pg_pool()
    if not pool:
        return None
    
    if app_id is None:
        app_id = os.getenv("APP_ID", "ppt-automate")
    
    try:
        row = await pool.fetchrow(
            """
            SELECT file_id, task_id, status, is_processing, updated_at 
            FROM user_ppt_metadata 
            WHERE user_id = $1 AND thread_id = $2 AND app_id = $3
            """,
            user_id, thread_id, app_id
        )
        
        if row:
            metadata = {
                "fileId": row["file_id"],
                "taskId": row["task_id"],
                "status": row["status"],
                "isProcessing": row["is_processing"],
                "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None
            }
            logger.info({
                "message": "Metadata retrieved",
                "user_id": user_id,
                "thread_id": thread_id,
                "app_id": app_id,
                "status": "success"
            })
            return metadata
        
        logger.info({
            "message": "Metadata not found",
            "user_id": user_id,
            "thread_id": thread_id,
            "app_id": app_id,
            "status": "not_found"
        })
        return None
        
    except Exception as e:
        logger.error({
            "message": "Failed to get metadata",
            "user_id": user_id,
            "thread_id": thread_id,
            "app_id": app_id,
            "error": str(e),
            "status": "error"
        })
        return None


async def save_ppt_metadata(
    user_id: str,
    thread_id: str,
    app_id: Optional[str] = None,
    file_id: Optional[str] = None,
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    is_processing: Optional[bool] = None
) -> bool:
    pool = await get_pg_pool()
    if not pool:
        return False
    
    if app_id is None:
        app_id = os.getenv("APP_ID", "ppt-automate")
    
    try:
        existing = await pool.fetchrow(
            "SELECT file_id, task_id, status, is_processing FROM user_ppt_metadata WHERE user_id = $1 AND thread_id = $2 AND app_id = $3",
            user_id, thread_id, app_id
        )
        
        if existing:
            update_fields = []
            params = [user_id, thread_id, app_id]
            param_idx = 4
            
            if file_id is not None:
                update_fields.append(f"file_id = ${param_idx}")
                params.append(file_id)
                param_idx += 1
            
            if task_id is not None:
                update_fields.append(f"task_id = ${param_idx}")
                params.append(task_id)
                param_idx += 1
            
            if status is not None:
                update_fields.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1
            
            if is_processing is not None:
                update_fields.append(f"is_processing = ${param_idx}")
                params.append(is_processing)
                param_idx += 1
            
            update_fields.append(f"updated_at = NOW()")
            
            if update_fields:
                query = f"""
                    UPDATE user_ppt_metadata 
                    SET {', '.join(update_fields)}
                    WHERE user_id = $1 AND thread_id = $2 AND app_id = $3
                """
                await pool.execute(query, *params)
        else:
            await pool.execute(
                """
                INSERT INTO user_ppt_metadata (user_id, thread_id, app_id, file_id, task_id, status, is_processing) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id, thread_id, app_id, file_id, task_id, status, is_processing if is_processing is not None else False
            )
        
        logger.info({
            "message": "Metadata saved",
            "user_id": user_id,
            "thread_id": thread_id,
            "app_id": app_id,
            "file_id": file_id,
            "task_id": task_id,
            "status": status,
            "is_processing": is_processing,
            "operation": "success"
        })
        
        return True
        
    except Exception as e:
        logger.error({
            "message": "Failed to save metadata",
            "user_id": user_id,
            "thread_id": thread_id,
            "app_id": app_id,
            "error": str(e),
            "status": "error"
        })
        return False

