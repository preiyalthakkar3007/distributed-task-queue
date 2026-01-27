# Distributed Task Queue

A high-performance distributed task queue system with support for priority scheduling, automatic retries, task dependencies, and persistent storage.

## Features

- **Priority-based scheduling** - High-priority tasks execute first
- **Automatic retry with exponential backoff** - Failed tasks retry automatically
- **Task dependencies** - Chain tasks that depend on each other
- **SQLite persistence** - Tasks survive system restarts
- **Multi-process workers** - Parallel task execution
- **Real-time web dashboard** - Monitor tasks through a browser interface
- **Command-line interface** - Easy management and monitoring

## Architecture

The system consists of four main components:

1. **Queue Manager** - Coordinates task submission and distribution
2. **Workers** - Execute tasks in separate processes
3. **Database** - Persists task state and results
4. **Dashboard** - Web interface for monitoring

## Installation
```bash
pip install flask
```

## Quick Start

### Submit and process tasks
```python
from queue_manager import TaskQueueManager
from worker import worker_process
import multiprocessing as mp

def my_task(x, y):
    return x + y

qm = TaskQueueManager()
task_id = qm.submit_task(my_task, args=(5, 3), priority=10)

stop_event = mp.Event()
p = mp.Process(target=worker_process, args=(1, qm.task_queue, qm.result_queue, stop_event))
p.start()
```

### Using the CLI

Start the dashboard with workers:
```bash
python cli.py dashboard -n 3 -p 5000
```

View statistics:
```bash
python cli.py stats
```

List all tasks:
```bash
python cli.py list
```

Start workers only:
```bash
python cli.py workers -n 4
```

## Task Dependencies

Create task pipelines where tasks wait for others to complete:
```python
task1 = qm.submit_task_with_dependency(download_file, args=("data.csv",))
task2 = qm.submit_task_with_dependency(process_file, depends_on=task1, args=("data.csv",))
task3 = qm.submit_task_with_dependency(upload_result, depends_on=task2, args=("result.csv",))
```

## Configuration

### Queue Manager Options

- `db_path` - SQLite database file location (default: "tasks.db")
- `recover` - Recover pending tasks on startup (default: True)

### Task Submission Options

- `priority` - Higher values execute first (default: 0)
- `max_retries` - Number of retry attempts (default: 3)
- `depends_on` - Task ID this task depends on (default: None)

## Use Cases

- **Data processing pipelines** - ETL workflows with dependencies
- **Batch job processing** - Process large datasets in parallel
- **Scheduled tasks** - Run periodic jobs with retry logic
- **API request handling** - Distribute API calls across workers
- **File processing** - Parallel image/video processing

## Technical Details

### Priority Queue

Tasks are executed based on priority. Higher priority values are processed first. Within the same priority, tasks follow FIFO order.

### Retry Logic

Failed tasks automatically retry with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay

### Persistence

All task metadata is stored in SQLite:
- Task ID and function name
- Arguments and priority
- Status and attempts
- Results and errors
- Creation and update timestamps

### Process Safety

The system uses multiprocessing-safe queues and shared dictionaries to coordinate between processes on Windows and Unix systems.

## Project Structure
```
distributed-task-queue/
├── task.py              # Task data model
├── queue_manager.py     # Queue coordination logic
├── worker.py            # Worker process implementation
├── database.py          # SQLite persistence layer
├── dashboard.py         # Flask web dashboard
├── cli.py               # Command-line interface
├── templates/
│   └── dashboard.html   # Dashboard UI
└── README.md
```

## Future Enhancements

- Task scheduling with cron-like syntax
- Worker health monitoring and auto-restart
- Task result caching
- Dead letter queue for permanently failed tasks
- Distributed workers across multiple machines
- Authentication for dashboard access

## License

MIT