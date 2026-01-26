import uuid
import time
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional


class TaskStatus(Enum):
    """All possible states a task can be in"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Task:
    """
    Represents a single unit of work.
    
    Example:
        def resize_image(path, width):
            # ... resize logic
            return "resized.jpg"
        
        task = Task(
            func=resize_image,
            args=("photo.jpg", 800),
            priority=5
        )
    """
    func: Callable              # The function to run
    args: tuple = ()           # Arguments to pass
    kwargs: dict = None        # Keyword arguments
    priority: int = 0          # Higher = more important
    max_retries: int = 3       # How many times to retry if it fails
    
    # Auto-assigned fields
    task_id: str = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    attempts: int = 0
    result: Any = None
    error: str = None
    
    def __post_init__(self):
        """Called automatically after __init__"""
        if self.task_id is None:
            self.task_id = str(uuid.uuid4())[:8]  # Short ID
        if self.created_at is None:
            self.created_at = time.time()
        if self.kwargs is None:
            self.kwargs = {}
    
    def execute(self):
        """
        Actually run the task.
        Returns: (success: bool, result: Any, error: str)
        """
        self.status = TaskStatus.RUNNING
        self.attempts += 1
        
        try:
            # Run the function
            result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            self.result = result
            return True, result, None
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.error = error_msg
            
            # Should we retry?
            if self.attempts < self.max_retries:
                self.status = TaskStatus.RETRYING
            else:
                self.status = TaskStatus.FAILED
            
            return False, None, error_msg
    
    def __repr__(self):
        return f"Task({self.task_id}, {self.func.__name__}, {self.status.value})"