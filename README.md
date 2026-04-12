# ⚙️ Distributed Task Queue

> Built from scratch in Python — priority scheduling, automatic retries, task dependency chains, multi-process workers, and a live monitoring dashboard. No Celery. No Redis. No magic.

[![Live Demo](https://img.shields.io/badge/🟢_LIVE_DEMO-View_Dashboard-green?style=for-the-badge)](https://distributed-task-queue-5iv0.onrender.com)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=flat-square&logo=sqlite)
![Multiprocessing](https://img.shields.io/badge/Concurrency-multiprocessing-orange?style=flat-square)

**[→ Open the live dashboard](https://distributed-task-queue-5iv0.onrender.com)** and watch tasks move through the pipeline in real time.

---

## The Problem

Every serious application eventually needs to run work in the background — sending emails, processing uploads, hitting slow third-party APIs, generating reports. If you do it inline, your server blocks. If you do it naively, a single failure cascades. If you don't prioritize, a low-stakes cron job can starve an urgent user-facing operation.

Production systems solve this with task queues. Tools like Celery and BullMQ are the industry standard — but they're also large, opinionated frameworks that abstract away the mechanisms underneath. This project builds those mechanisms from scratch: a process-safe priority queue, a worker pool, a retry engine, a persistence layer, and a real-time dashboard, all wired together without any queue middleware.

The goal wasn't to replace Celery. It was to understand exactly how these systems work — and to be able to explain it in an interview.

---

## What It Does

Submit a task → it gets queued by priority → a free worker picks it up → the result is recorded → if it fails, it retries → you watch all of it live on the dashboard.

```
┌─────────────────────────────────────────────────────────────┐
│                        PRODUCER                             │
│   qm.submit_task(func, priority=10, max_retries=3)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    QUEUE MANAGER                            │
│   Priority Queue  ──►  Task Registry  ──►  SQLite DB        │
│   (-priority, id, func, args)    Manager().dict()           │
└──────┬────────────────────────────────────────┬────────────-┘
       │                                        │
       ▼                                        ▼
┌──────────────────────┐             ┌──────────────────────┐
│   WORKER PROCESSES   │             │   FLASK DASHBOARD    │
│                      │             │                      │
│  Worker 1 ──► exec   │             │  GET /api/stats      │
│  Worker 2 ──► exec   │  results    │  GET /api/tasks      │
│  Worker 3 ──► exec   │──────────►  │                      │
│  Worker N ──► exec   │             │  Auto-refreshes 2s   │
└──────────────────────┘             └──────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   RESULT HANDLER │
              │  success → DONE  │
              │  failure → RETRY │
              │  exhausted → FAIL│
              └──────────────────┘
```

---

## Key Features

### ⚡ Priority Scheduling
Tasks aren't created equal. An urgent payment webhook shouldn't wait behind a weekly report. Each task gets a priority (higher = more urgent), and the queue guarantees ordering — always.

**Under the hood:** Tasks are enqueued as tuples `(-priority, task_id, func, args, kwargs)` into a `multiprocessing.Queue`. Python's tuple comparison does the heavy lifting: negating the priority flips the natural min-heap order so high-priority tasks always sort first. Task ID breaks ties within the same priority level, ensuring FIFO fairness.

```python
# Priority 10 executes before Priority 5, always
qm.submit_task(send_payment_webhook, priority=10)
qm.submit_task(generate_weekly_report, priority=5)
```

---

### 🔄 Automatic Retry
Transient failures happen — a network blip, a momentary database lock, a rate-limited API. Tasks that fail are automatically re-queued up to a configurable attempt limit. Once exhausted, they're marked FAILED and preserved for inspection.

**Under the hood:** Workers execute tasks inside a `try/except` and push results (including failures) to a separate `result_queue`. The main process drains this queue asynchronously, checks `attempts < max_retries`, and re-enqueues the task if there's runway left. The task keeps its original priority on retry, so high-priority work stays high-priority even after a failure.

```python
# Will try 4 times total before giving up
qm.submit_task(call_flaky_api, max_retries=3)
```

---

### 🔗 Task Dependency Chains
Some work has ordering requirements — you need the file downloaded before you process it, and processed before you upload the result. Tasks can declare a dependency on another task and will stay in `WAITING` status until their parent reaches `COMPLETED`.

**Under the hood:** Each task stores a `depends_on` field (a parent task ID). When any task completes, the system scans for waiting tasks that depend on it and promotes them to `PENDING`. No external scheduler needed — the queue manager handles it.

```python
# Classic ETL pipeline
t1 = qm.submit_task_with_dependency(download_file, args=("data.csv",))
t2 = qm.submit_task_with_dependency(clean_and_transform, depends_on=t1)
t3 = qm.submit_task_with_dependency(load_to_warehouse, depends_on=t2)
```

---

### 👷 Multi-Process Worker Pool
Workers are real OS processes — not threads, not coroutines. Each has its own Python interpreter and memory space, which means true parallelism even around the GIL. The pool size is configurable. Workers pick up tasks competitively from the shared queue: first available wins.

**Under the hood:** Workers run in a `while not stop_event.is_set()` loop. Each call to `task_queue.get(timeout=0.5)` blocks for up to 500ms before looping — this makes shutdown clean and responsive. A `multiprocessing.Event` signals graceful shutdown across all processes on Ctrl+C.

```bash
python cli.py dashboard -n 5   # Spin up 5 parallel workers
```

---

### 💾 Crash-Resistant Persistence
The queue survives restarts. Every task state change is immediately written to SQLite. On startup, incomplete tasks (PENDING, RUNNING, RETRYING) are automatically recovered from the database and re-queued for execution.

**Under the hood:** The system runs dual state: a `multiprocessing.Manager().dict()` for fast in-memory access during execution, and SQLite as the source of truth. Every update writes to both synchronously. `INSERT OR REPLACE` makes writes idempotent. Recovery at startup re-queues any task that was in-flight when the process died.

---

### 📊 Real-Time Dashboard
A live web dashboard shows every task — its status, priority, attempt count, result, and error — updated every 2 seconds without a page reload.

**Under the hood:** The dashboard is a vanilla JS frontend polling `/api/stats` and `/api/tasks` on a 2-second interval. Tasks are sorted client-side by a status priority order (running → retrying → pending → waiting → failed → completed), then by task priority, then by creation time. No WebSocket complexity — polling is simpler, works behind proxies, and 2 seconds is fast enough for human perception.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3 | Multiprocessing stdlib; no runtime dependencies for core queue |
| Concurrency | `multiprocessing` (stdlib) | Real OS processes, true parallelism, shared Queue and Event primitives |
| Storage | SQLite (stdlib) | Zero-config persistence; survives restarts without a database server |
| Web API | Flask | Lightweight; the dashboard is the secondary feature, not the core |
| Deployment | Render + Gunicorn | Free tier, easy Python hosting |

The core queue system — `task.py`, `queue_manager.py`, `worker.py`, `database.py` — has zero third-party dependencies. Flask is only needed if you want the dashboard.

---

## Running Locally

```bash
git clone https://github.com/preiyalthakkar3007/distributed-task-queue.git
cd distributed-task-queue
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install flask
```

**Quickest start — dashboard with sample tasks:**
```bash
python run_with_dashboard.py
# → http://localhost:5000
# Submits 4 sample tasks and runs 2 workers automatically
```

**CLI — configurable workers:**
```bash
python cli.py dashboard -n 3       # Dashboard + 3 workers
python cli.py workers -n 4         # Workers only, no web UI
python cli.py stats                # Print queue statistics
python cli.py list                 # List all tasks and their status
```

**Use it as a library:**
```python
from queue_manager import TaskQueueManager
import multiprocessing as mp
from worker import worker_process

def send_email(to, subject):
    # your logic here
    return f"Sent to {to}"

qm = TaskQueueManager(db_path="tasks.db", recover=True)

# Submit tasks with different priorities
qm.submit_task(send_email, args=("urgent@co.com", "Action Required"), priority=10)
qm.submit_task(send_email, args=("batch@co.com", "Newsletter"), priority=2, max_retries=3)

# Start workers
stop = mp.Event()
workers = []
for i in range(3):
    p = mp.Process(target=worker_process, args=(i, qm.task_queue, qm.result_queue, stop))
    p.start()
    workers.append(p)
```

**Run the test suite:**
```bash
python test_task.py          # Task execution and retry logic
python test_workers.py       # 3-worker pool integration test
python test_persistence.py   # Database recovery after restart
```

---

## Engineering Concepts Demonstrated

This project is a practical implementation of several distributed systems fundamentals:

### Concurrency Without a Framework
Rather than reaching for `asyncio` or a threading library, the system uses Python's `multiprocessing` module to achieve true parallelism. Workers are isolated OS processes — independent memory, independent GIL — communicating only through process-safe queues and a shared Manager dict. This is the same model production systems like Gunicorn's pre-fork worker use.

### Producer-Consumer Pattern
The queue manager is the producer; workers are consumers. They're fully decoupled — producers never wait for consumers, consumers never block producers. The `result_queue` separates result processing from task execution, so a slow result handler can't starve the worker pool. This is a textbook implementation of the producer-consumer pattern across process boundaries.

### Fault Tolerance via Retry
Fault-tolerant systems assume failure. The retry engine treats task failure as an expected state transition, not an exception. Failed tasks cycle through RETRYING → PENDING → RUNNING automatically, with the retry count tracked persistently so it survives process restarts. Once retries are exhausted, the task is preserved in FAILED state for inspection — it doesn't vanish.

### Durability and Recovery
The dual-state design (in-memory dict for speed, SQLite for durability) mirrors how production systems like Redis handle AOF persistence. The in-memory dict makes reads fast during execution; SQLite makes state durable across crashes. On startup, the recovery pass re-queues any task that was in flight when the process died — this is the distributed systems concept of "at-least-once delivery."

### Graceful Shutdown
Using `multiprocessing.Event` for shutdown signaling is a cleaner pattern than sending SIGTERM directly to worker PIDs. The stop event propagates across process boundaries without any signal handling boilerplate. Workers finish their current task, check the event, and exit cleanly. The main process joins with a timeout and hard-terminates any stragglers — the same pattern Kubernetes uses for pod termination.

### Priority Scheduling
The tuple-based priority trick (`(-priority, task_id, ...)`) is a common pattern in competitive programming and systems work. It exploits Python's stable, lexicographic tuple comparison to achieve min-heap behavior on a negated priority value — no custom comparator class needed. The task ID as a secondary sort key ensures deterministic FIFO ordering within the same priority level.

---

## Project Structure

```
distributed-task-queue/
├── task.py             # Task dataclass, TaskStatus enum
├── queue_manager.py    # Orchestration engine: submit, enqueue, retry, dependency resolution
├── worker.py           # Worker process loop: pull, execute, report
├── database.py         # SQLite persistence: save, load, recover
├── dashboard.py        # Flask API: /api/stats, /api/tasks
├── cli.py              # CLI: workers, dashboard, stats, list
├── run_with_dashboard.py  # One-command launcher with sample tasks
├── templates/
│   └── dashboard.html  # Single-file dashboard (vanilla JS, auto-polling)
├── test_task.py        # Unit tests: execution, retry logic
├── test_workers.py     # Integration: multi-worker pool
└── test_persistence.py # Integration: database recovery
```

---

*Built as an exercise in understanding what tools like Celery actually do under the hood — because the best way to understand a distributed system is to build one.*
