from task import Task
import time

# Simple test function
def add_numbers(a, b):
    time.sleep(1)  # Pretend this takes time
    return a + b

def failing_function():
    raise ValueError("This always fails!")

# Test 1: Successful task
task1 = Task(func=add_numbers, args=(5, 3))
print(f"Created: {task1}")

success, result, error = task1.execute()
print(f"Success: {success}, Result: {result}")
print(f"After execution: {task1}")
print()

# Test 2: Failing task with retries
task2 = Task(func=failing_function, max_retries=2)
print(f"Created: {task2}")

for i in range(3):
    success, result, error = task2.execute()
    print(f"Attempt {i+1}: {success}, Status: {task2.status.value}, Error: {error}")