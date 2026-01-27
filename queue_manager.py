import multiprocessing as mp
from multiprocessing import Queue, Manager
import time
import uuid
from typing import Dict, Any
from database import TaskDatabase


class TaskQueueManager:
    
    def __init__(self, db_path="tasks.db", recover=True):
        self.task_queue = Queue()
        self.result_queue = Queue()
        
        manager = Manager()
        self.tasks = manager.dict()
        self.stats = manager.dict({
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "running": 0
        })
        
        self.db = TaskDatabase(db_path)
        
        if recover:
            self.recover_tasks()
    
    def recover_tasks(self):
        pending_tasks = self.db.get_pending_tasks()
        
        if pending_tasks:
            print(f"\nRecovering {len(pending_tasks)} tasks from database...")
            
            for task_data in pending_tasks:
                task_data["status"] = "pending"
                self.tasks[task_data["task_id"]] = task_data
                
                print(f"  Recovered task {task_data['task_id']} - {task_data['func_name']}")
            
            print()
    
    def submit_task(self, func, args=(), kwargs=None, priority=0, max_retries=3):
        if kwargs is None:
            kwargs = {}
        
        task_id = str(uuid.uuid4())[:8]
        
        task_info = {
            "task_id": task_id,
            "func_name": func.__name__,
            "priority": priority,
            "max_retries": max_retries,
            "status": "pending",
            "depends_on": None,
            "attempts": 0,
            "result": None,
            "error": None,
            "created_at": time.time(),
            "args": args,
            "kwargs": kwargs
        }
        
        self.tasks[task_id] = task_info
        self.db.save_task(task_info)
        
        self.task_queue.put((-priority, task_id, func, args, kwargs, max_retries))
        
        self.stats["submitted"] += 1
        print(f"Task {task_id} submitted (priority: {priority})")
        
        return task_id
    
    def submit_task_with_dependency(self, func, depends_on=None, args=(), kwargs=None, priority=0, max_retries=3):
        if kwargs is None:
            kwargs = {}
        
        task_id = str(uuid.uuid4())[:8]
        
        task_info = {
            "task_id": task_id,
            "func_name": func.__name__,
            "priority": priority,
            "max_retries": max_retries,
            "status": "waiting" if depends_on else "pending",
            "depends_on": depends_on,
            "attempts": 0,
            "result": None,
            "error": None,
            "created_at": time.time(),
            "args": args,
            "kwargs": kwargs
        }
        
        self.tasks[task_id] = task_info
        self.db.save_task(task_info)
        
        if not depends_on:
            self.task_queue.put((-priority, task_id, func, args, kwargs, max_retries))
            self.stats["submitted"] += 1
            print(f"Task {task_id} submitted (priority: {priority})")
        else:
            print(f"Task {task_id} waiting for {depends_on} to complete")
        
        return task_id
    
    def check_dependent_tasks(self, completed_task_id):
        for task_id, task_info in list(self.tasks.items()):
            if task_info.get("status") == "waiting" and task_info.get("depends_on") == completed_task_id:
                task_info["status"] = "pending"
                self.tasks[task_id] = task_info
                self.db.save_task(task_info)
                
                print(f"Task {task_id} dependency satisfied, now pending")
    
    def get_stats(self):
        return dict(self.stats)
    
    def get_all_tasks(self):
        return self.db.get_all_tasks()
    
    def get_task_result(self, task_id: str):
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
                        print(f"Task {task_id} completed")
                        
                        self.check_dependent_tasks(task_id)
                    else:
                        task_info["error"] = result_data.get("error")
                        task_info["attempts"] += 1
                        
                        if task_info["attempts"] < task_info["max_retries"]:
                            task_info["status"] = "retrying"
                            self.task_queue.put((
                                -task_info["priority"],
                                task_id,
                                result_data["func"],
                                result_data["args"],
                                result_data["kwargs"],
                                task_info["max_retries"]
                            ))
                            print(f"Task {task_id} retrying ({task_info['attempts']}/{task_info['max_retries']})")
                        else:
                            task_info["status"] = "failed"
                            self.stats["failed"] += 1
                            print(f"Task {task_id} failed: {task_info['error']}")
                    
                    self.tasks[task_id] = task_info
                    self.db.save_task(task_info)
                    
            except Exception as e:
                print(f"Error processing result: {e}")
                break
    
    def close(self):
        self.db.close()