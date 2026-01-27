import time


def worker_process(worker_id, task_queue, result_queue, stop_event):
    print(f"[Worker {worker_id}] Started")
    
    while not stop_event.is_set():
        try:
            try:
                priority, task_id, func, args, kwargs, max_retries = task_queue.get(timeout=0.5)
            except:
                continue
            
            print(f"[Worker {worker_id}] Executing {task_id} - {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                
                result_queue.put({
                    "task_id": task_id,
                    "success": True,
                    "result": result,
                    "func": func,
                    "args": args,
                    "kwargs": kwargs
                })
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                result_queue.put({
                    "task_id": task_id,
                    "success": False,
                    "error": error_msg,
                    "func": func,
                    "args": args,
                    "kwargs": kwargs
                })
                
                time.sleep(0.5)
        
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}")
            time.sleep(0.5)
    
    print(f"[Worker {worker_id}] Stopped")