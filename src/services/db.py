from asyncio import Lock
import asyncio
import os
import threading
import asyncpg
from typing import Optional, Dict, Tuple

from src.logging import get_logger

logger = get_logger("db")

_POOLS: Dict[int, asyncpg.Pool] = {}
_POOL_LOCKS: Dict[int, Lock] = {}
_POOLS_META: Dict[int, Tuple[asyncpg.Pool, asyncio.AbstractEventLoop]] = {}
_POOLS_GUARD = threading.Lock()


async def get_pg_pool() -> Optional[asyncpg.Pool]:
    try:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
    except RuntimeError:
        logger.error({"message": "No running event loop found", "status": "error"})
        return None

    if loop_id in _POOLS:
        return _POOLS[loop_id]

    with _POOLS_GUARD:
        if loop_id not in _POOL_LOCKS:
            _POOL_LOCKS[loop_id] = Lock()

    conn_str = os.getenv("POSTGRES_CONN_STRING")
    if not conn_str:
        logger.error({"message": "POSTGRES_CONN_STRING environment variable not set", "status": "error"})
        return None
    conn_str = conn_str.replace("postgresql+psycopg://", "postgresql://")

    async with _POOL_LOCKS[loop_id]:
        if loop_id in _POOLS:
            return _POOLS[loop_id]

        try:
            if "options=" not in conn_str:
                if "?" in conn_str:
                    conn_str += "&options=-csearch_path%3Dpublic"
                else:
                    conn_str += "?options=-csearch_path%3Dpublic"
            
            pool = await asyncpg.create_pool(conn_str)
            with _POOLS_GUARD:
                _POOLS[loop_id] = pool
                _POOLS_META[loop_id] = (pool, loop)
            logger.info({"message": f"Database connection pool created for loop {loop_id}", "status": "success"})
            return pool
        except Exception as e:
            logger.error({"message": f"Failed to create database pool for loop {loop_id}", "error": str(e), "status": "error"})
            return None


async def close_pg_pool() -> None:
    try:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
    except RuntimeError:
        logger.warning({"message": "No running event loop found when closing pool", "status": "warning"})
        return

    pool = None
    with _POOLS_GUARD:
        pool = _POOLS.pop(loop_id, None)
        _POOLS_META.pop(loop_id, None)
        _POOL_LOCKS.pop(loop_id, None)

    if pool is not None:
        await pool.close()
        logger.info({"message": f"Database connection pool closed for loop {loop_id}", "status": "success"})


async def close_all_pools() -> None:
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    with _POOLS_GUARD:
        items = list(_POOLS_META.items())

    for loop_id, (pool, loop) in items:
        try:
            if current_loop is not None and loop is current_loop:
                await pool.close()
            else:
                fut = asyncio.run_coroutine_threadsafe(pool.close(), loop)
                fut.result()
            logger.info({"message": f"Database connection pool closed for loop {loop_id}", "status": "success"})
        except Exception as e:
            logger.error({"message": f"Error closing pool for loop {loop_id}", "error": str(e), "status": "error"})
        finally:
            with _POOLS_GUARD:
                _POOLS.pop(loop_id, None)
                _POOLS_META.pop(loop_id, None)
                _POOL_LOCKS.pop(loop_id, None)

    logger.info({"message": "All database connection pools closed", "status": "success"})


async def init_ppt_metadata_table() -> bool:
    try:
        pool = await get_pg_pool()
        if not pool:
            logger.error({"message": "Failed to get database pool for table initialization", "status": "error"})
            return False

        await pool.execute(
            """
            CREATE TABLE IF NOT EXISTS public.user_ppt_metadata (
                user_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                app_id TEXT NOT NULL,
                file_id TEXT,
                task_id TEXT,
                status TEXT,
                is_processing BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, thread_id, app_id)
            );
            """
        )

        await pool.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_ppt_metadata_user_thread 
            ON public.user_ppt_metadata(user_id, thread_id, created_at DESC);
            """
        )

        await pool.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_ppt_metadata_app 
            ON public.user_ppt_metadata(app_id, created_at DESC);
            """
        )

        logger.info({"message": "user_ppt_metadata table and indexes initialized successfully", "status": "success"})
        return True

    except Exception as e:
        logger.error({"message": "Failed to initialize user_ppt_metadata table", "error": str(e), "status": "error"})
        return False

