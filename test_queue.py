from queue_manager import QueueManager
from task import Task
import time

# Test functions
def task_a():
    print("  → Running Task A")
    time.sleep(1)
    return "A done"

def task_b():
    print("  → Running Task B")
    time.sleep(1)
    return "B done"

def task_c():
    print("  → Running Task C (high priority!)")
    time.sleep(1)
    return "C done"

# Create queue manager
qm = QueueManager()

# Submit tasks
print("Submitting tasks...\n")
task1 = Task(func=task_a, priority=1)
task2 = Task(func=task_b, priority=1)
task3 = Task(func=task_c, priority=10)  # High priority!

qm.submit_task(task1)
qm.submit_task(task2)
qm.submit_task(task3)

print("\n--- Queue Stats ---")
print(qm.get_stats())

print("\n--- All Tasks ---")
for t in qm.get_all_tasks():
    print(t)

# Manually execute tasks in priority order
print("\n--- Executing tasks ---")
while not qm.is_empty():
    task = qm.get_next_task()
    if task:
        print(f"\nExecuting: {task}")
        success, result, error = task.execute()
        qm.mark_completed(task.task_id, success, result, error)

print("\n--- Final Stats ---")
print(qm.get_stats())