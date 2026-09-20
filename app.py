import os
import json
import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request, session, Response
from flask_cors import CORS

from config.settings import SESSIONS_DIR, DISCLAIMER_TEXT, DEFAULT_OLLAMA_MODEL
from sensors.simulated import SimulatedHeartRateSensor
from sensors.ble_esp32 import ESP32BluetoothHeartRateSensor
from sensors.camera import camera_manager
from sensors.health import HardwareHealthChecker
from ai.ollama_client import OllamaClient
from core.assistant import StudyAssistant
from core.database import db_manager

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "flowmate_secret_key_2026_super_secure")
CORS(app)

# Application State Container
class AppState:
    def __init__(self):
        self.sensor_mode = "SIMULATION"  # "SIMULATION", "HARDWARE", "AUTO"
        self.simulated_sensor = SimulatedHeartRateSensor(initial_condition="DEEP_STUDY")
        self.hardware_sensor = ESP32BluetoothHeartRateSensor()
        self.active_sensor = self.simulated_sensor
        
        self.ollama_client = OllamaClient()
        self.assistant = StudyAssistant(sensor=self.active_sensor, ollama_client=self.ollama_client)
        
        self.session_state = "IDLE"  # "IDLE", "ACTIVE", "PAUSED"
        self.current_subject = "Mathematics"
        self.current_task = "Calculus - Integration"

    def set_sensor_mode(self, mode: str):
        mode = mode.upper()
        if mode in ["SIMULATION", "HARDWARE", "AUTO"]:
            self.sensor_mode = mode
            if mode == "SIMULATION":
                self.simulated_sensor.connect()
                self.active_sensor = self.simulated_sensor
            elif mode == "HARDWARE":
                self.hardware_sensor.connect()
                self.active_sensor = self.hardware_sensor
            elif mode == "AUTO":
                if self.hardware_sensor.is_connected():
                    self.active_sensor = self.hardware_sensor
                else:
                    self.simulated_sensor.connect()
                    self.active_sensor = self.simulated_sensor
            
            self.assistant.sensor = self.active_sensor
            return True
        return False

    def compute_focus_status(self, bpm: float, condition: str):
        if self.session_state == "IDLE":
            return "SESSION ENDED", "None", 0
        if self.session_state == "PAUSED":
            return "BREAK", "Low", 95
            
        if not self.active_sensor.is_connected():
            return "SENSOR OFFLINE", "None", 100
            
        if condition in ["DEEP_STUDY", "INTENSE_PROBLEM_SOLVING"]:
            return "FOCUSED", "High", 88
        elif condition == "RESTING_FOCUS":
            return "STUDYING", "Normal", 82
        elif condition == "FATIGUE_SLUMP":
            return "LOW ACTIVITY", "Low", 79
        elif condition == "DISTRACTED":
            return "LOW ACTIVITY", "Inconsistent", 75
        elif condition == "HIGH_STRESS_ANXIETY":
            return "STUDYING", "High (Strained)", 71
        else:
            return "STUDYING", "Normal", 80


state = AppState()
state.simulated_sensor.connect()

# Active logged in user roll no (default Arun 2026101)
DEFAULT_ROLL_NO = "2026101"

def get_current_roll_no():
    return session.get("roll_no", DEFAULT_ROLL_NO)


# Page route
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------------------------------------------
# AUTHENTICATION & USER MANAGEMENT ENDPOINTS
# -----------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.json or {}
    name = data.get("name", "").strip()
    roll_no = data.get("roll_no", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "Student").strip()

    if not name or not roll_no or not password:
        return jsonify({"success": False, "error": "Name, Roll Number, and Password are required."}), 400

    result = db_manager.register_user(name=name, roll_no=roll_no, password=password, role=role)
    if result.get("success"):
        session["roll_no"] = roll_no
    return jsonify(result)


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    roll_no = data.get("roll_no", "").strip()
    password = data.get("password", "").strip()

    if not roll_no or not password:
        return jsonify({"success": False, "error": "Roll Number and Password are required."}), 400

    result = db_manager.authenticate_user(roll_no=roll_no, password=password)
    if result.get("success"):
        session["roll_no"] = roll_no
    return jsonify(result)


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.pop("roll_no", None)
    return jsonify({"success": True})


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    roll_no = get_current_roll_no()
    user = db_manager.get_user_by_roll_no(roll_no)
    if not user:
        # Fallback default
        user = {
            "name": "Arun",
            "roll_no": "2026101",
            "role": "Student",
            "streak_days": 7,
            "goal_minutes": 180,
            "completed_minutes": 105
        }
    return jsonify({"success": True, "user": user, "use_mongodb": db_manager.use_mongodb})


# -----------------------------------------------------------------------------
# HARDWARE HEALTH & DIAGNOSTICS ENDPOINT
# -----------------------------------------------------------------------------

@app.route("/api/hardware/diagnostic", methods=["GET"])
def hardware_diagnostic():
    diag = HardwareHealthChecker.run_diagnostic(
        sensor=state.active_sensor,
        sensor_mode=state.sensor_mode
    )
    return jsonify({"success": True, "diagnostic": diag})


# -----------------------------------------------------------------------------
# CAMERA FEED & VISION TELEMETRY ENDPOINTS
# -----------------------------------------------------------------------------

@app.route("/api/camera/status", methods=["GET"])
def camera_status():
    return jsonify({"success": True, "camera": camera_manager.get_status()})


@app.route("/api/camera/toggle", methods=["POST"])
def camera_toggle():
    data = request.json or {}
    enable = data.get("enable", not camera_manager.is_active)
    if enable:
        success = camera_manager.start()
    else:
        camera_manager.stop()
        success = True
    return jsonify({"success": success, "camera": camera_manager.get_status()})


@app.route("/api/camera/stream")
def camera_stream():
    if not camera_manager.is_active:
        camera_manager.start()
    return Response(
        camera_manager.generate_mjpeg_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# -----------------------------------------------------------------------------
# CORE SYSTEM TELEMETRY & STATUS ENDPOINT
# -----------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def get_status():
    roll_no = get_current_roll_no()
    user = db_manager.get_user_by_roll_no(roll_no) or {
        "name": "Arun",
        "roll_no": "2026101",
        "goal_minutes": 180,
        "completed_minutes": 105,
        "streak_days": 7
    }
    
    session_active = state.assistant.session_active
    elapsed_sec = 0
    if session_active and state.assistant.start_time:
        elapsed_sec = int(time.time() - state.assistant.start_time)
        
    reading = state.assistant.record_sample() if session_active else None
    if not reading and state.simulated_sensor.is_connected():
        reading = state.simulated_sensor.get_reading()

    bpm = reading.bpm if reading else 72.0
    cond = reading.condition_label if reading else getattr(state.simulated_sensor, "_current_condition", "DEEP_STUDY")
    
    status_label, activity_level, confidence = state.compute_focus_status(bpm, cond)
    
    # Calculate focus score dynamically based on condition & BPM stability
    dynamic_focus_score = min(98, max(50, int(confidence + (10 if cond in ["DEEP_STUDY", "INTENSE_PROBLEM_SOLVING"] else 0))))
    user["focus_score"] = dynamic_focus_score

    return jsonify({
        "disclaimer": DISCLAIMER_TEXT,
        "database": {"using_mongodb": db_manager.use_mongodb},
        "student": user,
        "session": {
            "active": session_active,
            "state": state.session_state,
            "elapsed_seconds": elapsed_sec,
            "current_subject": state.current_subject,
            "current_task": state.current_task,
            "total_readings": len(state.assistant.readings),
            "average_bpm": round(state.assistant.get_average_bpm(), 1)
        },
        "sensor": {
            "mode": state.sensor_mode,
            "connected": state.active_sensor.is_connected(),
            "device_name": state.active_sensor.get_device_name(),
            "condition": cond,
            "bpm": bpm,
            "is_simulated": getattr(reading, "is_simulated", True)
        },
        "focus_analysis": {
            "status": status_label,
            "activity_level": activity_level,
            "confidence_pct": confidence,
            "recommended_break_min": 18
        }
    })


@app.route("/api/session/start", methods=["POST"])
def start_session():
    data = request.json or {}
    subject = data.get("subject", "Mathematics")
    task = data.get("task", "Calculus - Integration")
    
    state.current_subject = subject
    state.current_task = task
    
    success = state.assistant.start_session()
    if success:
        state.session_state = "ACTIVE"
        
    return jsonify({"success": success, "session_state": state.session_state})


@app.route("/api/session/pause", methods=["POST"])
def pause_session():
    if state.session_state == "ACTIVE":
        state.session_state = "PAUSED"
    elif state.session_state == "PAUSED":
        state.session_state = "ACTIVE"
    return jsonify({"success": True, "session_state": state.session_state})


@app.route("/api/session/stop", methods=["POST"])
def stop_session():
    saved_path = state.assistant.end_session()
    state.session_state = "IDLE"
    
    # Update user progress in database
    roll_no = get_current_roll_no()
    elapsed_min = max(1, int(state.assistant.get_session_duration_minutes()))
    db_manager.update_user_progress(roll_no, elapsed_min)
    
    return jsonify({
        "success": True,
        "session_state": "IDLE",
        "saved_file": str(saved_path) if saved_path else None
    })


@app.route("/api/sensor/read", methods=["GET"])
def sensor_read():
    reading = state.assistant.record_sample() if state.assistant.session_active else None
    if not reading and state.simulated_sensor.is_connected():
        reading = state.simulated_sensor.get_reading()
        
    if reading:
        bpm = reading.bpm
        cond = reading.condition_label
        device = reading.device_name
        is_sim = reading.is_simulated
    else:
        bpm = 72.0
        cond = getattr(state.simulated_sensor, "_current_condition", "DEEP_STUDY")
        device = state.active_sensor.get_device_name()
        is_sim = True

    status_label, activity_level, confidence = state.compute_focus_status(bpm, cond)
    
    return jsonify({
        "timestamp": time.time(),
        "bpm": bpm,
        "condition": cond,
        "device_name": device,
        "is_simulated": is_sim,
        "focus_status": status_label,
        "activity_level": activity_level,
        "confidence_pct": confidence
    })


@app.route("/api/sensor/condition", methods=["POST"])
def set_condition():
    data = request.json or {}
    condition = data.get("condition", "DEEP_STUDY")
    
    success = state.simulated_sensor.set_condition(condition)
    return jsonify({"success": success, "condition": condition})


@app.route("/api/sensor/mode", methods=["POST"])
def set_sensor_mode():
    data = request.json or {}
    mode = data.get("mode", "SIMULATION")
    
    success = state.set_sensor_mode(mode)
    return jsonify({"success": success, "mode": state.sensor_mode})


@app.route("/api/coach", methods=["POST"])
def ask_ai_coach():
    data = request.json or {}
    prompt_text = data.get("prompt", "")
    user_note = data.get("user_note", "")
    roll_no = get_current_roll_no()
    user = db_manager.get_user_by_roll_no(roll_no) or {"name": "Arun"}
    
    if prompt_text:
        res = state.ollama_client.generate_coaching(
            prompt=f"You are FlowMate AI Focus Coach. Provide concise, encouraging academic advice for student {user['name']} studying {state.current_subject}. Question: {prompt_text}"
        )
    else:
        res = state.assistant.request_ai_coaching(user_note=user_note)
        
    return jsonify(res)


@app.route("/api/study-plan", methods=["GET"])
def get_study_plan():
    roll_no = get_current_roll_no()
    tasks = db_manager.get_tasks(roll_no)
    if not tasks:
        # Seed default tasks if empty
        db_manager.add_task(roll_no, "Mathematics", "Calculus - Integration", 45)
        db_manager.add_task(roll_no, "Physics", "Electromagnetism & Waves", 30)
        db_manager.add_task(roll_no, "Programming", "Python Data Structures", 60)
        tasks = db_manager.get_tasks(roll_no)
    return jsonify({"tasks": tasks})


@app.route("/api/study-plan/task", methods=["POST"])
def update_study_task():
    data = request.json or {}
    task_id = data.get("id")
    action = data.get("action")  # "start", "pause", "complete", "add"
    roll_no = get_current_roll_no()
    
    if action == "add":
        subject = data.get("subject", "General")
        title = data.get("title", "Study Session")
        duration = int(data.get("duration", 30))
        db_manager.add_task(roll_no, subject, title, duration)
    elif action == "delete":
        if task_id:
            db_manager.delete_task(int(task_id))
    else:
        if task_id:
            db_manager.update_task_status(int(task_id), action)
        
    tasks = db_manager.get_tasks(roll_no)
    return jsonify({"success": True, "tasks": tasks})


@app.route("/api/progress", methods=["GET"])
def get_progress():
    roll_no = get_current_roll_no()
    user = db_manager.get_user_by_roll_no(roll_no) or {"completed_minutes": 105, "streak_days": 7}
    
    comp_hours = round(user.get("completed_minutes", 105) / 60, 1)
    
    return jsonify({
        "weekly_study_hours": [
            {"day": "Mon", "hours": 2.5},
            {"day": "Tue", "hours": 3.2},
            {"day": "Wed", "hours": 4.0},
            {"day": "Thu", "hours": 2.8},
            {"day": "Fri", "hours": 3.5},
            {"day": "Sat", "hours": 4.2},
            {"day": "Sun", "hours": comp_hours}
        ],
        "focus_trend": [
            {"time": "09:00", "score": 85},
            {"time": "10:00", "score": 92},
            {"time": "11:00", "score": 88},
            {"time": "12:00", "score": 65},
            {"time": "13:00", "score": 70},
            {"time": "14:00", "score": 84}
        ],
        "subject_distribution": [
            {"subject": "Mathematics", "pct": 40},
            {"subject": "Physics", "pct": 25},
            {"subject": "Programming", "pct": 20},
            {"subject": "Chemistry", "pct": 15}
        ],
        "summary": {
            "total_weekly_hours": round(21.95 + comp_hours, 1),
            "avg_focus_score": 84,
            "streak_days": user.get("streak_days", 7),
            "completed_tasks": 14
        }
    })


@app.route("/api/faculty/students", methods=["GET"])
def get_faculty_students():
    # Dynamic list combining database users
    students = [
        {
            "id": 101,
            "name": "Arun",
            "roll_no": "2026101",
            "status": "STUDYING",
            "focus_status": "FOCUSED",
            "subject": "Mathematics",
            "session_minutes": 48,
            "activity_level": "High",
            "today_progress": "1h 45m / 3h 00m",
            "sensor_status": "Connected (Simulated)",
            "alerts": []
        },
        {
            "id": 102,
            "name": "Priya S.",
            "roll_no": "2026102",
            "status": "STUDYING",
            "focus_status": "STUDYING",
            "subject": "Physics",
            "session_minutes": 25,
            "activity_level": "Normal",
            "today_progress": "2h 10m / 2h 30m",
            "sensor_status": "Connected (Hardware)",
            "alerts": []
        },
        {
            "id": 103,
            "name": "Karthik M.",
            "roll_no": "2026103",
            "status": "LOW ACTIVITY",
            "focus_status": "LOW ACTIVITY",
            "subject": "Programming",
            "session_minutes": 42,
            "activity_level": "Low",
            "today_progress": "0h 45m / 2h 00m",
            "sensor_status": "Connected (Simulated)",
            "alerts": ["⚠ Low Activity Detected (10m)"]
        }
    ]
    return jsonify({"students": students})


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    notifications = [
        {
            "id": 1,
            "category": "AI Recommendation",
            "title": "Optimal Focus Window",
            "message": "You are maintaining peak focus in Mathematics. Great time to try advanced integration problems!",
            "timestamp": time.time() - 600,
            "read": False
        },
        {
            "id": 2,
            "category": "Hardware Diagnostic",
            "title": "PPG Sensor Verified",
            "message": "Dynamic signal quality checked at 98.5% confidence.",
            "timestamp": time.time() - 1200,
            "read": False
        },
        {
            "id": 3,
            "category": "Study Reminder",
            "title": "Break Suggested Soon",
            "message": "You've been studying for 42 minutes continuous. Take a 5-minute break in 18 minutes.",
            "timestamp": time.time() - 1800,
            "read": True
        }
    ]
    return jsonify({"notifications": notifications})


@app.route("/api/notifications/read", methods=["POST"])
def mark_notification_read():
    return jsonify({"success": True})


@app.route("/api/sessions", methods=["GET"])
def get_session_history():
    sessions_list = []
    if SESSIONS_DIR.exists():
        for filepath in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    sessions_list.append({
                        "file_name": filepath.name,
                        "timestamp_start": content.get("timestamp_start"),
                        "duration_seconds": content.get("duration_seconds", 0),
                        "duration_formatted": f"{int(content.get('duration_seconds', 0)//60)}m {int(content.get('duration_seconds', 0)%60)}s",
                        "average_bpm": content.get("average_bpm"),
                        "total_readings": content.get("total_readings"),
                        "disclaimer": content.get("disclaimer")
                    })
            except Exception as e:
                print(f"[WARN] Failed to read {filepath.name}: {e}")
                
    return jsonify({"sessions": sessions_list})


@app.route("/api/sessions/<filename>", methods=["GET"])
def get_session_detail(filename):
    filepath = SESSIONS_DIR / filename
    if filepath.exists() and filepath.is_file():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    return jsonify({"error": "Session file not found"}), 404


if __name__ == "__main__":
    print("=" * 70)
    print("       FLOWMATE AI STUDY-FOCUS ASSISTANT - WEB SERVER")
    print("=" * 70)
    print("Running web interface at: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

