from flask import Flask, render_template, jsonify, request
from queue_manager import TaskQueueManager
import threading
import time

app = Flask(__name__)

qm = None
workers = []
stop_event = None


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    if qm:
        stats = qm.get_stats()
        return jsonify(stats)
    return jsonify({"error": "Queue not initialized"})


@app.route('/api/tasks')
def get_tasks():
    if qm:
        tasks = qm.get_all_tasks()
        return jsonify(tasks)
    return jsonify([])


@app.route('/api/task/<task_id>')
def get_task(task_id):
    if qm:
        result = qm.get_task_result(task_id)
        return jsonify(result)
    return jsonify({"error": "Queue not initialized"})


def result_processor():
    while True:
        if qm and stop_event and not stop_event.is_set():
            qm.process_results()
        time.sleep(0.5)


def start_dashboard(queue_manager, port=5000):
    global qm
    qm = queue_manager
    
    processor_thread = threading.Thread(target=result_processor, daemon=True)
    processor_thread.start()
    
    app.run(host='0.0.0.0', port=port, debug=False)