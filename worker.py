import time


def worker_process(worker_id, task_queue, result_queue, stop_event):
    """
    Worker that pulls tasks from queue and executes them.
    
    Args:
        worker_id: Identifier for this worker
        task_queue: Queue to pull tasks from
        result_queue: Queue to push results to
        stop_event: Signal to stop working
    """
    print(f"[Worker {worker_id}] Started")
    
    while not stop_event.is_set():
        try:
            # Try to get a task (timeout so we can check stop_event)
            try:
                priority, task_id, func, args, kwargs, max_retries = task_queue.get(timeout=0.5)
            except:
                # Queue empty or timeout, continue
                continue
            
            print(f"[Worker {worker_id}] Executing {task_id} - {func.__name__}")
            
            # Execute the task
            try:
                result = func(*args, **kwargs)
                
                # Report success
                result_queue.put({
                    "task_id": task_id,
                    "success": True,
                    "result": result,
                    "func": func,
                    "args": args,
                    "kwargs": kwargs
                })
                
            except Exception as e:
                # Report failure
                error_msg = f"{type(e).__name__}: {str(e)}"
                result_queue.put({
                    "task_id": task_id,
                    "success": False,
                    "error": error_msg,
                    "func": func,
                    "args": args,
                    "kwargs": kwargs
                })
                
                # Exponential backoff before retry
                time.sleep(0.5)
        
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}")
            time.sleep(0.5)
    
    print(f"[Worker {worker_id}] Stopped")