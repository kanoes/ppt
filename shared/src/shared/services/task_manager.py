import asyncio
import uuid
from typing import Dict, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TaskStatus:
    """Task status"""
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = 0  # 0-100
    message: str = ""
    file_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class TaskManager:
    """Singleton task manager"""
    _instance = None
    _tasks: Dict[str, TaskStatus] = {}
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._tasks = {}
            self._initialized = True
    
    async def create_task(self, task_id: Optional[str] = None) -> str:
        """Create new task and return task ID"""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        async with self._lock:
            self._tasks[task_id] = TaskStatus(
                task_id=task_id,
                status="pending",
                progress=0,
                message="Task created, waiting for processing"
            )
        return task_id
    
    async def update_task(
        self,
        task_id: str,
        status: Optional[Literal["pending", "processing", "completed", "failed"]] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        file_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update task status"""
        async with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} does not exist")
            
            task = self._tasks[task_id]
            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if message is not None:
                task.message = message
            if file_id is not None:
                task.file_id = file_id
            if error is not None:
                task.error = error
            task.updated_at = datetime.now()
    
    async def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        async with self._lock:
            return self._tasks.get(task_id)
    
    async def delete_task(self, task_id: str):
        """Delete task (optional, for cleaning up old tasks)"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
    
    async def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Clean up completed tasks that are older than the specified time"""
        now = datetime.now()
        async with self._lock:
            tasks_to_delete = []
            for task_id, task in self._tasks.items():
                if task.status in ["completed", "failed"]:
                    age = (now - task.updated_at).total_seconds()
                    if age > max_age_seconds:
                        tasks_to_delete.append(task_id)
            
            for task_id in tasks_to_delete:
                del self._tasks[task_id]


# Global task manager instance
task_manager = TaskManager()

