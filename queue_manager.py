import multiprocessing as mp
from multiprocessing import Queue, Manager
import time
import uuid
from typing import Dict, Any
from database import TaskDatabase


class TaskQueueManager:
    """
    Windows-compatible task queue with SQLite persistence.
    """
    
    def __init__(self, db_path="tasks.db", recover=True):
        # Shared queues for communication
        self.task_queue = Queue()
        self.result_queue = Queue()
        
        # Shared state using Manager
        manager = Manager()
        self.tasks = manager.dict()
        self.stats = manager.dict({
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "running": 0
        })
        
        # Database for persistence
        self.db = TaskDatabase(db_path)
        
        # Recover pending tasks from database
        if recover:
            self._recover_tasks()
    
    def _recover_tasks(self):
        """
        Recover pending/running tasks from database on restart.
        """
        pending_tasks = self.db.get_pending_tasks()
        
        if pending_tasks:
            print(f"\n🔄 Recovering {len(pending_tasks)} tasks from database...")
            
            for task_data in pending_tasks:
                # Note: We can't recover the actual function objects
                # In a real system, you'd use a task registry
                task_data["status"] = "pending"  # Reset status
                self.tasks[task_data["task_id"]] = task_data
                
                print(f"  ↻ Recovered task {task_data['task_id']} - {task_data['func_name']}")
                
                # TODO: Re-queue tasks (would need function registry)
            
            print()
    
    def submit_task(self, func, args=(), kwargs=None, priority=0, max_retries=3):
        """Submit a task to the queue."""
        if kwargs is None:
            kwargs = {}
        
        task_id = str(uuid.uuid4())[:8]
        
        task_info = {
            "task_id": task_id,
            "func_name": func.__name__,
            "priority": priority,
            "max_retries": max_retries,
            "status": "pending",
            "attempts": 0,
            "result": None,
            "error": None,
            "created_at": time.time(),
            "args": args,
            "kwargs": kwargs
        }
        
        # Save to memory
        self.tasks[task_id] = task_info
        
        # Save to database
        self.db.save_task(task_info)
        
        # Put in queue
        self.task_queue.put((-priority, task_id, func, args, kwargs, max_retries))
        
        self.stats["submitted"] += 1
        print(f"✓ Task {task_id} submitted (priority: {priority})")
        
        return task_id
    
    def get_stats(self):
        """Get current statistics."""
        return dict(self.stats)
    
    def get_all_tasks(self):
        """Get all task info from database."""
        return self.db.get_all_tasks()
    
    def get_task_result(self, task_id: str):
        """Get result of a specific task."""
        task = self.db.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "result": task["result"],
            "error": task["error"]
        }
    
    def process_results(self):
        """Process completed task results from result queue."""
        while not self.result_queue.empty():
            try:
                result_data = self.result_queue.get_nowait()
                task_id = result_data["task_id"]
                success = result_data["success"]
                
                if task_id in self.tasks:
                    task_info = dict(self.tasks[task_id])
                    
                    if success:
                        task_info["status"] = "completed"
                        task_info["result"] = result_data.get("result")
                        self.stats["completed"] += 1
                        print(f"✓ Task {task_id} completed")
                    else:
                        task_info["error"] = result_data.get("error")
                        task_info["attempts"] += 1
                        
                        # Retry logic
                        if task_info["attempts"] < task_info["max_retries"]:
                            task_info["status"] = "retrying"
                            # Re-queue the task
                            self.task_queue.put((
                                -task_info["priority"],
                                task_id,
                                result_data["func"],
                                result_data["args"],
                                result_data["kwargs"],
                                task_info["max_retries"]
                            ))
                            print(f"↻ Task {task_id} retrying ({task_info['attempts']}/{task_info['max_retries']})")
                        else:
                            task_info["status"] = "failed"
                            self.stats["failed"] += 1
                            print(f"✗ Task {task_id} failed: {task_info['error']}")
                    
                    # Update both memory and database