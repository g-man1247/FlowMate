import os
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import DATA_DIR, SESSIONS_DIR

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "flowmate_db"

LOCAL_DB_FILE = DATA_DIR / "db_store.json"

class DatabaseManager:
    """
    MongoDB Database Manager for FlowMate.
    Automatically connects to MongoDB if available, or seamlessly uses persistent local DB.
    Handles User Authentication, Study Tasks, Session Logs, and Notifications.
    """

    def __init__(self):
        self.use_mongodb = False
        self.client = None
        self.db = None
        
        # Try connecting to MongoDB
        try:
            import pymongo
            self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=1500)
            # Trigger server info request to verify connection
            self.client.server_info()
            self.db = self.client[DB_NAME]
            self.use_mongodb = True
            print("[INFO] Successfully connected to MongoDB database.")
        except Exception as e:
            print(f"[NOTICE] MongoDB not detected locally ({e}). Using persistent Local JSON DB.")
            self.use_mongodb = False
            self._init_local_db()

        self._seed_default_data()

    def _init_local_db(self):
        """Initialize local file store if MongoDB is not running."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not LOCAL_DB_FILE.exists():
            initial_data = {
                "users": [],
                "tasks": [],
                "notifications": []
            }
            with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def _read_local_db(self) -> Dict[str, Any]:
        if not LOCAL_DB_FILE.exists():
            self._init_local_db()
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_local_db(self, data: Dict[str, Any]):
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _seed_default_data(self):
        """Seed initial default users if database is empty."""
        default_users = [
            {
                "name": "Arun",
                "roll_no": "2026101",
                "password": self._hash_password("password123"),
                "role": "Student",
                "streak_days": 7,
                "goal_minutes": 180,
                "completed_minutes": 105,
                "created_at": time.time()
            },
            {
                "name": "Priya S.",
                "roll_no": "2026102",
                "password": self._hash_password("password123"),
                "role": "Student",
                "streak_days": 5,
                "goal_minutes": 150,
                "completed_minutes": 130,
                "created_at": time.time()
            },
            {
                "name": "Karthik M.",
                "roll_no": "2026103",
                "password": self._hash_password("password123"),
                "role": "Student",
                "streak_days": 3,
                "goal_minutes": 120,
                "completed_minutes": 45,
                "created_at": time.time()
            },
            {
                "name": "Prof. Sundar",
                "roll_no": "FAC2026",
                "password": self._hash_password("admin123"),
                "role": "Faculty",
                "streak_days": 30,
                "goal_minutes": 0,
                "completed_minutes": 0,
                "created_at": time.time()
            }
        ]

        if self.use_mongodb:
            users_col = self.db["users"]
            if users_col.count_documents({}) == 0:
                users_col.insert_many(default_users)
                print("[INFO] MongoDB seeded with default users.")
        else:
            local = self._read_local_db()
            if not local.get("users"):
                local["users"] = default_users
                self._write_local_db(local)

    # -------------------------------------------------------------------------
    # USER AUTHENTICATION & MANAGEMENT
    # -------------------------------------------------------------------------

    def register_user(self, name: str, roll_no: str, password: str, role: str = "Student") -> Dict[str, Any]:
        """Register a new student or faculty member manually."""
        hashed = self._hash_password(password)
        user_doc = {
            "name": name,
            "roll_no": roll_no.strip(),
            "password": hashed,
            "role": role,
            "streak_days": 1,
            "goal_minutes": 180,
            "completed_minutes": 0,
            "created_at": time.time()
        }

        if self.use_mongodb:
            users_col = self.db["users"]
            if users_col.find_one({"roll_no": roll_no}):
                return {"success": False, "error": "Roll Number already registered."}
            users_col.insert_one(user_doc)
        else:
            local = self._read_local_db()
            if any(u["roll_no"] == roll_no for u in local["users"]):
                return {"success": False, "error": "Roll Number already registered."}
            local["users"].append(user_doc)
            self._write_local_db(local)

        # Remove password hash from response
        user_info = {k: v for k, v in user_doc.items() if k != "password" and k != "_id"}
        return {"success": True, "user": user_info}

    def authenticate_user(self, roll_no: str, password: str) -> Dict[str, Any]:
        """Authenticate user by Roll No and Password."""
        hashed = self._hash_password(password)
        roll_no = roll_no.strip()

        if self.use_mongodb:
            users_col = self.db["users"]
            user = users_col.find_one({"roll_no": roll_no, "password": hashed})
            if not user:
                return {"success": False, "error": "Invalid Roll Number or Password."}
            user_info = {k: v for k, v in user.items() if k != "password" and k != "_id"}
        else:
            local = self._read_local_db()
            user = next((u for u in local["users"] if u["roll_no"] == roll_no and u["password"] == hashed), None)
            if not user:
                return {"success": False, "error": "Invalid Roll Number or Password."}
            user_info = {k: v for k, v in user.items() if k != "password"}

        return {"success": True, "user": user_info}

    def get_user_by_roll_no(self, roll_no: str) -> Optional[Dict[str, Any]]:
        """Fetch user document by Roll No."""
        if self.use_mongodb:
            user = self.db["users"].find_one({"roll_no": roll_no})
            if user:
                return {k: v for k, v in user.items() if k != "password" and k != "_id"}
            return None
        else:
            local = self._read_local_db()
            user = next((u for u in local["users"] if u["roll_no"] == roll_no), None)
            if user:
                return {k: v for k, v in user.items() if k != "password"}
            return None

    def update_user_progress(self, roll_no: str, added_minutes: int):
        """Update completed study minutes for a user."""
        if self.use_mongodb:
            self.db["users"].update_one(
                {"roll_no": roll_no},
                {"$inc": {"completed_minutes": added_minutes}}
            )
        else:
            local = self._read_local_db()
            for u in local["users"]:
                if u["roll_no"] == roll_no:
                    u["completed_minutes"] = u.get("completed_minutes", 0) + added_minutes
                    break
            self._write_local_db(local)

    # -------------------------------------------------------------------------
    # TASKS MANAGEMENT
    # -------------------------------------------------------------------------

    def get_tasks(self, roll_no: str) -> List[Dict[str, Any]]:
        """Get tasks for a specific user."""
        if self.use_mongodb:
            tasks = list(self.db["tasks"].find({"roll_no": roll_no}))
            for t in tasks:
                t["_id"] = str(t["_id"])
            return tasks
        else:
            local = self._read_local_db()
            return [t for t in local.get("tasks", []) if t.get("roll_no") == roll_no]

    def add_task(self, roll_no: str, subject: str, title: str, duration_minutes: int) -> Dict[str, Any]:
        """Add a new study task."""
        new_task = {
            "id": int(time.time() * 1000),
            "roll_no": roll_no,
            "subject": subject,
            "title": title,
            "duration_minutes": duration_minutes,
            "completed_minutes": 0,
            "status": "NOT_STARTED",
            "progress_pct": 0,
            "created_at": time.time()
        }

        if self.use_mongodb:
            self.db["tasks"].insert_one(new_task)
            new_task["_id"] = str(new_task["_id"])
        else:
            local = self._read_local_db()
            local.setdefault("tasks", []).append(new_task)
            self._write_local_db(local)

        return new_task

    def update_task_status(self, task_id: int, action: str) -> bool:
        """Update task status."""
        if self.use_mongodb:
            task = self.db["tasks"].find_one({"id": task_id})
            if task:
                new_status = "COMPLETED" if action == "complete" else ("IN_PROGRESS" if action == "start" else "PAUSED")
                pct = 100 if action == "complete" else (70 if action == "start" else task.get("progress_pct", 0))
                comp_min = task["duration_minutes"] if action == "complete" else task.get("completed_minutes", 0)
                
                self.db["tasks"].update_one(
                    {"id": task_id},
                    {"$set": {"status": new_status, "progress_pct": pct, "completed_minutes": comp_min}}
                )
                return True
        else:
            local = self._read_local_db()
            for t in local.get("tasks", []):
                if t["id"] == task_id:
                    if action == "complete":
                        t["status"] = "COMPLETED"
                        t["progress_pct"] = 100
                        t["completed_minutes"] = t["duration_minutes"]
                    elif action == "start":
                        t["status"] = "IN_PROGRESS"
                    elif action == "pause":
                        t["status"] = "PAUSED"
                    self._write_local_db(local)
                    return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """Delete task by ID."""
        if self.use_mongodb:
            result = self.db["tasks"].delete_one({"id": task_id})
            return result.deleted_count > 0
        else:
            local = self._read_local_db()
            tasks = local.get("tasks", [])
            initial_count = len(tasks)
            local["tasks"] = [t for t in tasks if t["id"] != task_id]
            if len(local["tasks"]) < initial_count:
                self._write_local_db(local)
                return True
        return False


# Singleton instance
db_manager = DatabaseManager()
