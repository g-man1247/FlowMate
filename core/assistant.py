import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import SESSIONS_DIR, DISCLAIMER_TEXT
from sensors.base import BaseHeartRateSensor, HeartRateReading
from ai.ollama_client import OllamaClient
from ai.prompts import build_coaching_prompt
from core.statistics import calculate_session_statistics


class StudyAssistant:
    """
    Main orchestrator for study focus sessions.
    
    Coordinates sensor sampling, session data accumulation, Ollama focus coaching,
    and non-medical disclaimer enforcement.
    """

    def __init__(
        self,
        sensor: BaseHeartRateSensor,
        ollama_client: Optional[OllamaClient] = None,
        session_dir: Path = SESSIONS_DIR
    ):
        self.sensor = sensor
        self.ollama = ollama_client or OllamaClient()
        self.session_dir = session_dir
        self.session_active = False
        self.start_time: Optional[float] = None
        self.readings: List[HeartRateReading] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start_session(self) -> bool:
        """Start a new study focus session."""
        if not self.sensor.is_connected():
            if not self.sensor.connect():
                print("[ERROR] Failed to connect to heart rate sensor.")
                return False

        self.session_active = True
        self.start_time = time.time()
        self.readings.clear()
        print("\n[INFO] Study Session Started.")
        print(f"[NOTICE] {DISCLAIMER_TEXT}\n")
        return True

    def record_sample(self) -> Optional[HeartRateReading]:
        """Poll the sensor and record the latest sample."""
        if not self.session_active:
            return None

        reading = self.sensor.get_reading()
        if reading:
            self.readings.append(reading)
        return reading

    def get_session_duration_minutes(self) -> int:
        """Calculate elapsed session duration in minutes."""
        if not self.start_time:
            return 0
        elapsed_sec = time.time() - self.start_time
        return max(1, int(elapsed_sec // 60))

    def get_average_bpm(self) -> float:
        """Calculate average heart rate recorded during current session."""
        if not self.readings:
            return 0.0
        return sum(r.bpm for r in self.readings) / len(self.readings)

    def request_ai_coaching(self, user_note: str = "") -> Dict[str, Any]:
        """
        Request focus coaching feedback from Ollama based strictly on explicit session metrics.
        Does NOT perform medical analysis or allow metric hallucination.
        """
        # 1. Calculate session statistics independently of sensor origin
        stats = calculate_session_statistics(self.readings)
        
        # 2. Extract condition and recent readings string block
        if not self.readings:
            simulated_condition = getattr(self.sensor, "_current_condition", "Information unavailable")
            recent_readings_fmt = []
        else:
            simulated_condition = self.readings[-1].condition_label
            # Format up to 5 most recent readings explicitly
            recent_slice = self.readings[-5:]
            recent_readings_fmt = [
                f"Time: {time.strftime('%H:%M:%S', time.localtime(r.timestamp))} | "
                f"BPM: {r.bpm:.1f} | Condition: {r.condition_label} [Simulated]"
                for r in recent_slice
            ]

        # 3. Build grounded prompt
        prompt_text = build_coaching_prompt(
            stats=stats,
            simulated_condition=simulated_condition,
            recent_readings=recent_readings_fmt,
            user_note=user_note,
        )

        # 4. Dispatch to Ollama
        return self.ollama.generate_coaching(prompt=prompt_text)

    def end_session(self) -> Optional[Path]:
        """End session, stop continuous monitoring, stop sensor, and save JSON log in data/sessions/."""
        if not self.session_active:
            return None

        self.stop_continuous_monitoring()
        self.session_active = False
        end_time = time.time()
        duration_sec = round(end_time - (self.start_time or end_time), 1)

        self.sensor.disconnect()

        session_data = {
            "disclaimer": DISCLAIMER_TEXT,
            "timestamp_start": self.start_time,
            "timestamp_end": end_time,
            "duration_seconds": duration_sec,
            "total_readings": len(self.readings),
            "average_bpm": round(self.get_average_bpm(), 1),
            "readings": [
                {
                    "bpm": r.bpm,
                    "timestamp": r.timestamp,
                    "is_simulated": r.is_simulated,
                    "condition_label": r.condition_label,
                    "device_name": r.device_name,
                }
                for r in self.readings
            ],
        }

        # Save to data/sessions/ session_<timestamp>.json
        file_name = f"session_{int(self.start_time or time.time())}.json"
        save_path = self.session_dir / file_name
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

        print(f"[INFO] Study Session Ended. Summary saved to: {save_path}")
        return save_path

    def start_continuous_monitoring(
        self,
        poll_interval: float = 2.0,
        ai_interval: float = 30.0,
        print_callback=None
    ) -> bool:
        """Start a background thread to continuously poll sensor and request AI coaching."""
        if not self.session_active:
            if not self.start_session():
                return False

        if self._monitor_thread and self._monitor_thread.is_alive():
            return True

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(poll_interval, ai_interval, print_callback),
            daemon=True
        )
        self._monitor_thread.start()
        print("[INFO] Continuous monitoring started.")
        return True

    def stop_continuous_monitoring(self) -> None:
        """Stop the continuous monitoring background thread safely."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            print("[INFO] Continuous monitoring stopped.")

    def _monitoring_loop(self, poll_interval: float, ai_interval: float, print_callback) -> None:
        """Background loop executing continuous sensor reading and periodic AI coaching."""
        last_ai_time = time.time()

        while not self._stop_event.is_set():
            # 1. Record sample
            reading = self.record_sample()
            if reading and print_callback:
                print_callback(f"-> {reading}")

            # 2. Check if AI interval has elapsed
            current_time = time.time()
            if (current_time - last_ai_time) >= ai_interval:
                if print_callback:
                    print_callback("\n[AUTO-AI] Requesting periodic focus coaching...")
                
                res = self.request_ai_coaching(user_note="Automatic periodic check")
                if res.get("success") and print_callback:
                    print_callback("\n" + "=" * 50)
                    print_callback("AI FOCUS COACH FEEDBACK:")
                    print_callback("=" * 50)
                    print_callback(res.get("response"))
                    print_callback("=" * 50 + "\n")
                elif print_callback:
                    print_callback(f"\n[Ollama Notice] {res.get('error')}\n")
                
                last_ai_time = current_time

            # 3. Wait for next poll interval
            # Use small sleeps to allow quick exit when stop_event is set
            sleep_duration = min(poll_interval, 0.5)
            elapsed = 0.0
            while elapsed < poll_interval and not self._stop_event.is_set():
                time.sleep(sleep_duration)
                elapsed += sleep_duration
