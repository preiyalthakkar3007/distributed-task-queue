import time
import multiprocessing as mp
from queue_manager import TaskQueueManager
from worker import worker_process


# Example task functions
def quick_task(name):
    print(f"    → Quick task '{name}' starting")
    time.sleep(1)
    return f"{name} completed!"


def slow_task(name):
    print(f"    → Slow task '{name}' starting")
    time.sleep(3)
    return f"{name} completed!"


def failing_task(name):
    print(f"    → Failing task '{name}' attempting...")
    raise ValueError(f"{name} always fails!")


if __name__ == "__main__":
    print("=== Creating Queue Manager ===\n")
    qm = TaskQueueManager()
    
    print("=== Submitting Tasks ===\n")
    qm.submit_task(quick_task, args=("Task-1",), priority=5)
    qm.submit_task(slow_task, args=("Task-2",), priority=1)
    qm.submit_task(quick_task, args=("Task-3",), priority=10)  # High priority!
    qm.submit_task(quick_task, args=("Task-4",), priority=5)
    qm.submit_task(failing_task, args=("Task-5",), priority=3, max_retries=2)
    qm.submit_task(slow_task, args=("Task-6",), priority=1)
    
    print("\n=== Starting 3 Workers ===\n")
    
    # Create stop event
    stop_event = mp.Event()
    
    # Start worker processes
    workers = []
    for i in range(3):
        p = mp.Process(
            target=worker_process,
            args=(i+1, qm.task_queue, qm.result_queue, stop_event)
        )
        p.start()
        workers.append(p)
    
    print("\n=== Workers Processing Tasks ===\n")
    
    # Monitor for 12 seconds, processing results
    start_time = time.time()
    while time.time() - start_time < 12:
        qm.process_results()
        time.sleep(0.5)
    
    # Stop workers
    print("\n=== Stopping Workers ===\n")
    stop_event.set()
    
    for p in workers:
        p.join(timeout=2)
        if p.is_alive():
            p.terminate()
    
    # Process any remaining results
    qm.process_results()
    
    # Show final stats
    print("\n=== Final Statistics ===")
    stats = qm.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n=== All Tasks ===")
    for task in qm.get_all_tasks():
        print(f"  [{task['status']}] {task['task_id']} - {task['func_name']} (priority: {task['priority']})")