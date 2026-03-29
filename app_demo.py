from flask import Flask, render_template, jsonify
import threading
import time
import uuid
import random

app = Flask(__name__)

TASK_NAMES = [
    "ingest_user_events",
    "process_payment_batch",
    "send_email_digest",
    "sync_inventory_db",
    "generate_daily_report",
    "compress_log_files",
    "fetch_exchange_rates",
    "train_recommendation_model",
    "backup_postgres_snapshot",
    "resize_uploaded_images",
    "run_fraud_detection",
    "aggregate_analytics",
    "purge_expired_sessions",
    "index_search_documents",
    "notify_webhook_subscribers",
]

tasks = {}
stats = {"submitted": 0, "running": 0, "completed": 0, "failed": 0}
lock = threading.Lock()


def make_task(status=None, depends_on=None):
    task_id = str(uuid.uuid4())[:8]
    priority = random.choice([1, 2, 3, 5, 8, 10])
    max_retries = random.choice([2, 3, 5])
    attempts = 0
    if status in ("retrying", "failed", "completed"):
        attempts = random.randint(1, max_retries)
    return {
        "task_id": task_id,
        "func_name": random.choice(TASK_NAMES),
        "priority": priority,
        "max_retries": max_retries,
        "status": status or "pending",
        "depends_on": depends_on,
        "attempts": attempts,
        "result": "ok" if status == "completed" else None,
        "error": "TimeoutError: upstream unavailable" if status in ("failed", "retrying") else None,
        "created_at": time.time() - random.randint(0, 120),
    }


def seed_tasks():
    with lock:
        for _ in range(4):
            t = make_task("completed")
            tasks[t["task_id"]] = t
            stats["submitted"] += 1
            stats["completed"] += 1
        for _ in range(2):
            t = make_task("failed")
            tasks[t["task_id"]] = t
            stats["submitted"] += 1
            stats["failed"] += 1
        for _ in range(2):
            t = make_task("retrying")
            tasks[t["task_id"]] = t
            stats["submitted"] += 1
        for _ in range(3):
            t = make_task("running")
            tasks[t["task_id"]] = t
            stats["submitted"] += 1
            stats["running"] += 1
        for _ in range(3):
            t = make_task("pending")
            tasks[t["task_id"]] = t
            stats["submitted"] += 1
        t1 = make_task("completed")
        tasks[t1["task_id"]] = t1
        t2 = make_task("running", depends_on=t1["task_id"])
        tasks[t2["task_id"]] = t2
        t3 = make_task("waiting", depends_on=t2["task_id"])
        tasks[t3["task_id"]] = t3
        stats["submitted"] += 3
        stats["completed"] += 1
        stats["running"] += 1


def lifecycle():
    while True:
        time.sleep(random.uniform(1.5, 3.0))
        with lock:
            task_list = list(tasks.values())

            running = [t for t in task_list if t["status"] == "running"]
            if running:
                t = random.choice(running)
                if random.random() < 0.82:
                    t["status"] = "completed"
                    t["result"] = "ok"
                    stats["completed"] += 1
                    for other in task_list:
                        if other["status"] == "waiting" and other.get("depends_on") == t["task_id"]:
                            other["status"] = "pending"
                else:
                    t["attempts"] += 1
                    if t["attempts"] < t["max_retries"]:
                        t["status"] = "retrying"
                    else:
                        t["status"] = "failed"
                        t["error"] = random.choice([
                            "TimeoutError: upstream unavailable",
                            "ConnectionRefusedError: port 5432",
                            "MemoryError: OOM on worker-2",
                            "ValueError: schema mismatch",
                        ])
                        stats["failed"] += 1
                stats["running"] = max(0, stats["running"] - 1)
                tasks[t["task_id"]] = t

            pending = [t for t in task_list if t["status"] == "pending"]
            if pending:
                t = max(pending, key=lambda x: x["priority"])
                t["status"] = "running"
                stats["running"] += 1
                tasks[t["task_id"]] = t

            retrying = [t for t in task_list if t["status"] == "retrying"]
            if retrying:
                t = random.choice(retrying)
                t["status"] = "running"
                stats["running"] += 1
                tasks[t["task_id"]] = t

            if random.random() < 0.5:
                new_task = make_task("pending")
                tasks[new_task["task_id"]] = new_task
                stats["submitted"] += 1

            if len(tasks) > 30:
                completed_ids = [tid for tid, t in tasks.items() if t["status"] == "completed"]
                if completed_ids:
                    del tasks[random.choice(completed_ids)]


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/stats")
def get_stats():
    with lock:
        return jsonify(dict(stats))


@app.route("/api/tasks")
def get_tasks():
    with lock:
        sorted_tasks = sorted(
            tasks.values(),
            key=lambda t: (
                ["running", "retrying", "pending", "waiting", "failed", "completed"].index(t["status"]),
                -t["priority"],
                -t["created_at"],
            ),
        )
        return jsonify(list(sorted_tasks))


seed_tasks()
threading.Thread(target=lifecycle, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
