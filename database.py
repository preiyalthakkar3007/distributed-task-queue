import sqlite3
import json
import time
from typing import Dict, List


class TaskDatabase:
    
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
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
                depends_on TEXT,
                attempts INTEGER,
                result TEXT,
                error TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        self.conn.commit()
    
    def save_task(self, task_data: Dict):
        cursor = self.conn.cursor()
        
        task_data["updated_at"] = time.time()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks 
            (task_id, func_name, args, kwargs, priority, max_retries, 
             status, depends_on, attempts, result, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data["task_id"],
            task_data["func_name"],
            json.dumps(task_data.get("args", [])),
            json.dumps(task_data.get("kwargs", {})),
            task_data["priority"],
            task_data["max_retries"],
            task_data["status"],
            task_data.get("depends_on"),
            task_data["attempts"],
            json.dumps(task_data.get("result")),
            task_data.get("error"),
            task_data.get("created_at", time.time()),
            task_data["updated_at"]
        ))
        
        self.conn.commit()
    
    def get_task(self, task_id: str) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self.row_to_dict(row)
    
    def get_all_tasks(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        return [self.row_to_dict(row) for row in rows]
    
    def get_pending_tasks(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE status IN ('pending', 'running', 'retrying')
            ORDER BY priority DESC
        """)
        rows = cursor.fetchall()
        
        return [self.row_to_dict(row) for row in rows]
    
    def delete_task(self, task_id: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        self.conn.commit()
    
    def clear_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks")
        self.conn.commit()
    
    def row_to_dict(self, row) -> Dict:
        return {
            "task_id": row[0],
            "func_name": row[1],
            "args": json.loads(row[2]),
            "kwargs": json.loads(row[3]),
            "priority": row[4],
            "max_retries": row[5],
            "status": row[6],
            "depends_on": row[7],
            "attempts": row[8],
            "result": json.loads(row[9]) if row[9] else None,
            "error": row[10],
            "created_at": row[11],
            "updated_at": row[12]
        }
    
    def close(self):
        self.conn.close()