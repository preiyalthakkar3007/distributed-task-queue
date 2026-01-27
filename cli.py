import argparse
import time
import multiprocessing as mp
from queue_manager import TaskQueueManager
from worker import worker_process
from dashboard import start_dashboard


def start_workers_cmd(args):
    qm = TaskQueueManager(db_path=args.database, recover=True)
    
    print(f"Starting {args.workers} workers...")
    
    stop_event = mp.Event()
    workers = []
    
    for i in range(args.workers):
        p = mp.Process(target=worker_process, args=(i+1, qm.task_queue, qm.result_queue, stop_event))
        p.start()
        workers.append(p)
    
    print(f"Workers started. Processing tasks from {args.database}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            qm.process_results()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping workers...")
        stop_event.set()
        for p in workers:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        qm.close()
        print("Workers stopped")


def start_dashboard_cmd(args):
    qm = TaskQueueManager(db_path=args.database, recover=True)
    
    stop_event = mp.Event()
    workers = []
    
    print(f"Starting {args.workers} workers...")
    for i in range(args.workers):
        p = mp.Process(target=worker_process, args=(i+1, qm.task_queue, qm.result_queue, stop_event))
        p.start()
        workers.append(p)
    
    print(f"Dashboard starting at http://localhost:{args.port}")
    print("Press Ctrl+C to stop\n")
    
    try:
        start_dashboard(qm, port=args.port)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        for p in workers:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
        qm.close()


def show_stats_cmd(args):
    qm = TaskQueueManager(db_path=args.database, recover=False)
    
    stats = qm.get_stats()
    print("\nQueue Statistics:")
    print(f"  Submitted: {stats['submitted']}")
    print(f"  Running:   {stats['running']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed:    {stats['failed']}")
    
    qm.close()


def list_tasks_cmd(args):
    qm = TaskQueueManager(db_path=args.database, recover=False)
    
    tasks = qm.get_all_tasks()
    
    if not tasks:
        print("\nNo tasks found")
        qm.close()
        return
    
    print(f"\nFound {len(tasks)} tasks:\n")
    
    for task in tasks:
        depends = f" (depends on {task['depends_on']})" if task.get('depends_on') else ""
        print(f"[{task['status'].upper():10}] {task['task_id']} - {task['func_name']} (priority: {task['priority']}){depends}")
        if task.get('error'):
            print(f"             Error: {task['error']}")
    
    qm.close()


def main():
    parser = argparse.ArgumentParser(
        description='Distributed Task Queue Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--database', default='tasks.db', help='Database file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    worker_parser = subparsers.add_parser('workers', help='Start worker processes')
    worker_parser.add_argument('-n', '--workers', type=int, default=3, help='Number of workers')
    worker_parser.set_defaults(func=start_workers_cmd)
    
    dashboard_parser = subparsers.add_parser('dashboard', help='Start web dashboard with workers')
    dashboard_parser.add_argument('-n', '--workers', type=int, default=2, help='Number of workers')
    dashboard_parser.add_argument('-p', '--port', type=int, default=5000, help='Dashboard port')
    dashboard_parser.set_defaults(func=start_dashboard_cmd)
    
    stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
    stats_parser.set_defaults(func=show_stats_cmd)
    
    list_parser = subparsers.add_parser('list', help='List all tasks')
    list_parser.set_defaults(func=list_tasks_cmd)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()