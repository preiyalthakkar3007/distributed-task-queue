import uuid
import time
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    WAITING = "waiting"


@dataclass
class Task:
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: int = 0
    max_retries: int = 3
    
    task_id: str = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    attempts: int = 0
    result: Any = None
    error: str = None
    
    def __post_init__(self):
        if self.task_id is None:
            self.task_id = str(uuid.uuid4())[:8]
        if self.created_at is None:
            self.created_at = time.time()
        if self.kwargs is None:
            self.kwargs = {}
    
    def execute(self):
        self.status = TaskStatus.RUNNING
        self.attempts += 1
        
        try:
            result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            self.result = result
            return True, result, None
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.error = error_msg
            
            if self.attempts < self.max_retries:
                self.status = TaskStatus.RETRYING
            else:
                self.status = TaskStatus.FAILED
            
            return False, None, error_msg
    
    def __repr__(self):
        return f"Task({self.task_id}, {self.func.__name__}, {self.status.value})"