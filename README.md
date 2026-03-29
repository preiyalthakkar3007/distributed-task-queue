# ⚙️ Distributed Task Queue

> A production-grade task queue system built from scratch — priority scheduling, automatic retries, dependency chains, and a live monitoring dashboard.

[![Live Demo](https://img.shields.io/badge/🟢_LIVE_DEMO-distributed--task--queue.onrender.com-green?style=for-the-badge)](https://distributed-task-queue-5iv0.onrender.com)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-persistent-blue?style=flat-square&logo=sqlite)

---

## What It Does

Most apps need background jobs — sending emails, processing uploads, running reports. This system handles all of it with priority queuing, fault tolerance, and real-time visibility.

**[Open the live dashboard →](https://distributed-task-queue-5iv0.onrender.com)** and watch tasks flow through the pipeline in real time.

---

## Features

| Feature | Details |
|---------|---------|
| ⚡ **Priority Scheduling** | Higher priority tasks always execute first |
| 🔄 **Auto Retry + Backoff** | Failed tasks retry automatically (configurable attempts) |
| 🔗 **Task Dependencies** | Chain tasks that wait for others to complete |
| 💾 **SQLite Persistence** | Tasks survive server restarts |
| 👷 **Multi-process Workers** | Parallel execution across worker processes |
| 📊 **Live Dashboard** | Real-time monitoring via Flask web UI |
| 🖥️ **CLI Interface** | Submit and manage tasks from the terminal |

---

## Architecture
```
Producer → Queue Manager → Worker Processes → Result Handler
                ↓                                    ↓
           SQLite DB ←──────────────────────── Status Updates
                ↓
          Flask Dashboard (real-time polling)
```

---

## Quick Start
```bash
git clone https://github.com/preiyalthakkar3007/distributed-task-queue.git
cd distributed-task-queue
pip install flask
```

### Submit tasks programmatically
```python
from queue_manager import TaskQueueManager

def process_data(x, y):
    return x + y

qm = TaskQueueManager()
qm.submit_task(process_data, args=(5, 3), priority=10)
```

### Create dependency chains
```python
t1 = qm.submit_task_with_dependency(download_file, args=("data.csv",))
t2 = qm.submit_task_with_dependency(process_file, depends_on=t1)
t3 = qm.submit_task_with_dependency(upload_result, depends_on=t2)
```

### Run via CLI
```bash
python cli.py dashboard -n 3   # Start dashboard with 3 workers
python cli.py stats            # View queue statistics
python cli.py list             # List all tasks
```

---

## Retry Logic

Failed tasks automatically retry with exponential backoff:
```
Attempt 1 → immediate
Attempt 2 → 2s delay
Attempt 3 → 4s delay
... then marked as FAILED
```

---

## Tech Stack

- **Language:** Python
- **Queue:** multiprocessing.Queue (process-safe)
- **Storage:** SQLite
- **Dashboard:** Flask + vanilla JS (auto-refreshes every 2s)
- **Deployment:** Render

---

## Use Cases

- ETL data pipelines with dependencies
- Batch job processing
- Distributed API request handling
- Parallel file/image processing
- Any background job workload

---

*Built as an alternative to Celery for understanding distributed systems fundamentals.*
