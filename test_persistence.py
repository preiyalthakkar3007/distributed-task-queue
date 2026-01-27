import time
import multiprocessing as mp
from queue_manager import TaskQueueManager
from worker import worker_process


def sample_task(name, duration=1):
    print(f"    → Task '{name}' running for {duration}s")
    time.sleep(duration)
    return f"{name} done!"


if __name__ == "__main__":
    print("=== TEST 1: Submit tasks and let them run ===\n")
    
    # Create queue (will create tasks.db)
    qm = TaskQueueManager(db_path="tasks.db", recover=False)
    
    # Submit tasks
    qm.submit_task(sample_task, args=("Alpha", 2), priority=5)
    qm.submit_task(sample_task, args=("Beta", 1), priority=10)
    qm.submit_task(sample_task, args=("Gamma", 3), priority=3)
    
    # Start workers
    stop_event = mp.Event()
    workers = []
    for i in range(2):
        p = mp.Process(target=worker_process, args=(i+1, qm.task_queue, qm.result_queue, stop_event))
        p.start()
        workers.append(p)
    
    # Let them run for 5 seconds
    print("\n=== Running for 5 seconds... ===\n")
    for _ in range(10):
        qm.process_results()
        time.sleep(0.5)
    
    # Stop
    stop_event.set()
    for p in workers:
        p.join(timeout=2)
        if p.is_alive():
            p.terminate()
    
    qm.process_results()
    qm.close()
    
    print("\n" + "="*50)
    print("=== TEST 2: Restart and check database ===\n")
    
    # Create new queue manager - should recover tasks
    qm2 = TaskQueueManager(db_path="tasks.db", recover=True)
    
    print("\n=== All tasks from database ===")
    all_tasks = qm2.get_all_tasks()
    for task in all_tasks:
        print(f"  [{task['status']}] {task['task_id']} - {task['func_name']} | Result: {task['result']}")
    
    print(f"\n Database persistence working! Found {len(all_tasks)} tasks.")
    qm2.close()