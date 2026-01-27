import time
import multiprocessing as mp
from queue_manager import TaskQueueManager
from worker import worker_process
from dashboard import start_dashboard
import threading


def sample_task(name, duration=2):
    print(f"    Task '{name}' running for {duration}s")
    time.sleep(duration)
    return f"{name} completed"


def failing_task(name):
    print(f"    Failing task '{name}' attempting")
    raise ValueError(f"{name} failed")


if __name__ == "__main__":
    qm = TaskQueueManager(db_path="tasks.db", recover=False)
    
    qm.submit_task(sample_task, args=("Task-A", 3), priority=5)
    qm.submit_task(sample_task, args=("Task-B", 2), priority=10)
    qm.submit_task(failing_task, args=("Task-C",), priority=3, max_retries=2)
    qm.submit_task(sample_task, args=("Task-D", 1), priority=7)
    
    stop_event = mp.Event()
    
    workers = []
    for i in range(2):
        p = mp.Process(target=worker_process, args=(i+1, qm.task_queue, qm.result_queue, stop_event))
        p.start()
        workers.append(p)
    
    print("\nStarting dashboard at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    try:
        start_dashboard(qm, port=5000)
    except KeyboardInterrupt:
        print("\nStopping workers...")
        stop_event.set()
        for p in workers:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        qm.close()