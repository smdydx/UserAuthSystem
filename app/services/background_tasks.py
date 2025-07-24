
"""
Background Task System for FastAPI
"""
import asyncio
import logging
from typing import Callable, Any, Dict, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class Task:
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    result: Any = None
    error: str = None
    retries: int = 0
    max_retries: int = 3

class BackgroundTaskManager:
    """Simple background task manager"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []
        self.running = False
        self.worker_task = None
    
    async def add_task(self, func: Callable, *args, name: str = None, max_retries: int = 3, **kwargs) -> str:
        """Add task to queue"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            created_at=datetime.now(),
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        self.queue.append(task_id)
        
        # Start worker if not running
        if not self.running:
            await self.start_worker()
        
        logger.info(f"Task {task_id} ({task.name}) added to queue")
        return task_id
    
    async def start_worker(self):
        """Start background worker"""
        if self.running:
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Background task worker started")
    
    async def stop_worker(self):
        """Stop background worker"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background task worker stopped")
    
    async def _worker(self):
        """Worker coroutine"""
        while self.running:
            if self.queue:
                task_id = self.queue.pop(0)
                task = self.tasks.get(task_id)
                
                if task and task.status == TaskStatus.PENDING:
                    await self._execute_task(task)
            else:
                await asyncio.sleep(1)  # Wait for new tasks
    
    async def _execute_task(self, task: Task):
        """Execute a single task"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"Executing task {task.id} ({task.name})")
            
            # Execute the function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.now()
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.retries += 1
            
            if task.retries < task.max_retries:
                task.status = TaskStatus.RETRY
                self.queue.append(task.id)  # Re-queue for retry
                logger.warning(f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(f"Task {task.id} failed permanently: {e}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error,
            "retries": task.retries
        }

# Global task manager
task_manager = BackgroundTaskManager()

# Decorator for background tasks
def background_task(name: str = None, max_retries: int = 3):
    """Decorator to run function as background task"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await task_manager.add_task(
                func, *args, 
                name=name or func.__name__, 
                max_retries=max_retries,
                **kwargs
            )
        return wrapper
    return decorator

# Usage examples
@background_task(name="send_email", max_retries=5)
async def send_welcome_email(user_email: str, user_name: str):
    """Background task for sending emails"""
    # Simulate email sending
    await asyncio.sleep(2)
    logger.info(f"Welcome email sent to {user_email}")
    return {"status": "sent", "email": user_email}

@background_task(name="process_order", max_retries=3)
async def process_order_background(order_id: int):
    """Background task for order processing"""
    # Simulate order processing
    await asyncio.sleep(5)
    logger.info(f"Order {order_id} processed")
    return {"order_id": order_id, "status": "processed"}
