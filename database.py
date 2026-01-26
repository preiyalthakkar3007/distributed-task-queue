import sqlite3
import json
import time
from typing import Dict, List, Any


class TaskDatabase:
    """
    Persists tasks to SQLite so they survive restarts.
    """
    
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create the tasks table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                func_name TEXT NOT NULL,
                args TEXT,
                kwargs TEXT,
                priority INTEGER,
                max_retries INTEGER,
                status TEXT,
                attempts INTEGER,
                result TEXT,
                error TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        self.conn.commit()
    
    def save_task(self, task_data: Dict):
        """Save or update a task."""
        cursor = self.conn.cursor()
        
        task_data["updated_at"] = time.time()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks 
            (task_id, func_name, args, kwargs, priority, max_retries, 
             status, attempts, result, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data["task_id"],
            task_data["func_name"],
            json.dumps(task_data.get("args", [])),
            json.dumps(task_data.get("kwargs", {})),
            task_data["priority"],
            task_data["max_retries"],
            task_data["status"],
            task_data["attempts"],
            json.dumps(task_data.get("result")),
            task_data.get("error"),
            task_data.get("created_at", time.time()),
            task_data["updated_at"]
        ))
        
        self.conn.commit()
    
    def get_task(self, task_id: str) -> Dict:
        """Get a single task by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks (for recovery on restart)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE status IN ('pending', 'running', 'retrying')
            ORDER BY priority DESC
        """)
        rows = cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def delete_task(self, task_id: str):
        """Delete a task."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        self.conn.commit()
    
    def clear_all_tasks(self):
        """Clear all tasks (for testing)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks")
        self.conn.commit()
    
    def _row_to_dict(self, row) -> Dict:
        """Convert SQLite row to dictionary."""
        return {
            "task_id": row[0],
            "func_name": row[1],
            "args": json.loads(row[2]),
            "kwargs": json.loads(row[3]),
            "priority": row[4],
            "max_retries": row[5],
            "status": row[6],
            "attempts": row[7],
            "result": json.loads(row[8]) if row[8] else None,
            "error": row[9],
            "created_at": row[10],
            "updated_at": row[11]
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()