"""
FlowMate Camera Feed & Vision Focus Telemetry Service using OpenCV.
Supports OpenCV 4.x (CascadeClassifier / Haar) and OpenCV 5.x (FaceDetectorYN / YuNet).

Includes real-time vision telemetry for:
- Eye closure & drowsiness detection
- Head turn & gaze alignment tracking
- Mobile phone / looking-down distraction detection
- Presence / Away-from-screen detection
- Session distraction report logging
"""

import os
import time
import threading
import urllib.request
import numpy as np
from typing import Dict, Any, Optional, List
import cv2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)

# YuNet ONNX model for OpenCV 5+ face detection & 5-point facial landmarks
YUNET_MODEL_PATH = os.path.join(_PROJECT_ROOT, "face_detection_yunet.onnx")
YUNET_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
)


def _download_yunet_model() -> bool:
    """Download YuNet ONNX model if not already present."""
    if os.path.exists(YUNET_MODEL_PATH):
        return True
    try:
        print(f"[INFO] Downloading YuNet face detection model to {YUNET_MODEL_PATH} ...")
        urllib.request.urlretrieve(YUNET_MODEL_URL, YUNET_MODEL_PATH)
        print(f"[INFO] YuNet model downloaded ({os.path.getsize(YUNET_MODEL_PATH)} bytes).")
        return True
    except Exception as e:
        print(f"[WARN] Could not download YuNet model: {e}. Face detection disabled.")
        return False


def _build_face_detector():
    """Build detector appropriate for OpenCV version."""
    major_ver = int(cv2.__version__.split(".")[0])

    if major_ver < 5 and hasattr(cv2, "CascadeClassifier"):
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if os.path.exists(cascade_path):
                det = cv2.CascadeClassifier(cascade_path)
                if not det.empty():
                    print("[INFO] Face detector: Haar CascadeClassifier (OpenCV 4.x)")
                    return det, "haar"
        except Exception as e:
            print(f"[WARN] Haar cascade failed: {e}")

    if hasattr(cv2, "FaceDetectorYN_create"):
        if _download_yunet_model():
            try:
                det = cv2.FaceDetectorYN_create(
                    YUNET_MODEL_PATH,
                    "",
                    (320, 320),
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5,
                )
                print("[INFO] Face detector: YuNet FaceDetectorYN (OpenCV 5.x)")
                return det, "yunet"
            except Exception as e:
                print(f"[WARN] YuNet detector init failed: {e}")

    print("[WARN] No face detector available — stream will work without vision analysis.")
    return None, None


class CameraFeedManager:
    """
    Manages live webcam video capture, MJPEG streaming, advanced vision monitoring
    (eyes closed, head turned, phone/looking down, away from screen), and session distraction reporting.
    """

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.is_active = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = threading.Lock()

        # Build face detector
        self.face_detector, self._detector_mode = _build_face_detector()

        # Telemetry & Distraction States
        self.last_face_detected = False
        self.last_posture = "NO CAMERA"
        self.current_alert = "NORMAL"
        self.eyes_closed_start_time: Optional[float] = None
        self.away_start_time: Optional[float] = None
        
        # Distraction Counters & Event Logs
        self.distraction_counts = {
            "eyes_closed": 0,
            "turned_away": 0,
            "looking_down_mobile": 0,
            "away_from_screen": 0,
        }
        self.distraction_events: List[Dict[str, Any]] = []
        self.last_recorded_alert: Optional[str] = None
        self.alert_cooldown: Dict[str, float] = {}

    def start(self) -> bool:
        """Initialize webcam hardware capture."""
        with self.lock:
            if self.is_active:
                return True
            try:
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.camera_id)

                if self.cap.isOpened():
                    self.is_active = True
                    self.last_posture = "UPRIGHT FOCUS"
                    self.current_alert = "NORMAL"
                    self.away_start_time = None
                    print(f"[INFO] Camera {self.camera_id} opened successfully.")
                    return True
                else:
                    self.is_active = False
                    self.last_posture = "CAMERA OFFLINE"
                    self.current_alert = "OFFLINE"
                    return False
            except Exception as e:
                print(f"[ERROR] Camera start error: {e}")
                self.is_active = False
                self.last_posture = "CAMERA ERROR"
                self.current_alert = "ERROR"
                return False

    def stop(self) -> None:
        """Release webcam capture cleanly."""
        with self.lock:
            self.is_active = False
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.last_posture = "CAMERA STOPPED"
            self.last_face_detected = False
            self.current_alert = "STOPPED"
            print("[INFO] Camera stopped.")

    def get_status(self) -> Dict[str, Any]:
        """Return real-time vision telemetry status & distraction report."""
        return {
            "enabled": True,
            "active": self.is_active,
            "camera_id": self.camera_id,
            "face_detected": self.last_face_detected,
            "posture_label": self.last_posture if self.is_active else "CAMERA STOPPED",
            "alert": self.current_alert if self.is_active else "STOPPED",
            "status": "OPERATIONAL" if self.is_active else "STOPPED",
            "detector_mode": self._detector_mode or "none",
            "distraction_summary": self.get_distraction_report(),
        }

    def get_distraction_report(self) -> Dict[str, Any]:
        """Return total distraction metrics for report generation."""
        total = sum(self.distraction_counts.values())
        return {
            "total_distractions": total,
            "counts": self.distraction_counts.copy(),
            "recent_events": self.distraction_events[-10:]
        }

    def _log_distraction(self, alert_type: str, message: str):
        """Log a distraction event with cooldown to prevent flood."""
        now = time.time()
        last_time = self.alert_cooldown.get(alert_type, 0)
        if (now - last_time) > 4.0:  # 4 second cooldown per alert category
            self.alert_cooldown[alert_type] = now
            if alert_type in self.distraction_counts:
                self.distraction_counts[alert_type] += 1
            self.distraction_events.append({
                "timestamp": now,
                "time_formatted": time.strftime("%H:%M:%S", time.localtime(now)),
                "type": alert_type,
                "message": message
            })
            print(f"[VISION ALERT] {alert_type.upper()}: {message}")

    # ------------------------------------------------------------------
    # Vision & Landmark Analysis Engine
    # ------------------------------------------------------------------

    def _analyze_eye_closure(self, frame, eye_r, eye_l) -> bool:
        """
        Check if eyes are closed by analyzing crop intensity around eye landmarks.
        Returns True if eyes appear closed.
        """
        h, w = frame.shape[:2]
        r_x, r_y = int(eye_r[0]), int(eye_r[1])
        l_x, l_y = int(eye_l[0]), int(eye_l[1])

        # Define small crop boxes around left & right eyes
        crop_size = 12
        r_box = frame[max(0, r_y-crop_size):min(h, r_y+crop_size), max(0, r_x-crop_size):min(w, r_x+crop_size)]
        l_box = frame[max(0, l_y-crop_size):min(h, l_y+crop_size), max(0, l_x-crop_size):min(w, l_x+crop_size)]

        if r_box.size == 0 or l_box.size == 0:
            return False

        r_gray = cv2.cvtColor(r_box, cv2.COLOR_BGR2GRAY)
        l_gray = cv2.cvtColor(l_box, cv2.COLOR_BGR2GRAY)

        # Eye open typically has dark pupil center vs skin. Low variance/flat intensity = eyes closed.
        r_var = np.var(r_gray)
        l_var = np.var(l_gray)
        
        # If both eye crops have low spatial contrast variance, eyes are closed
        return (r_var < 110.0 and l_var < 110.0)

    def _analyze_yunet_detection(self, frame, det):
        """
        Analyze 15-parameter YuNet detection array:
        [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rm, y_rm, x_lm, y_lm, score]
        """
        x, y, w, h = int(det[0]), int(det[1]), int(det[2]), int(det[3])
        eye_r = (det[4], det[5])
        eye_l = (det[6], det[7])
        nose = (det[8], det[9])

        frame_h, frame_w = frame.shape[:2]

        # 1. Check head turn (yaw offset: relative position of nose between eyes)
        eye_center_x = (eye_r[0] + eye_l[0]) / 2.0
        eye_dist = max(1.0, abs(eye_l[0] - eye_r[0]))
        yaw_offset = abs(nose[0] - eye_center_x) / eye_dist

        # 2. Check looking down / phone use (pitch offset: nose vertical position)
        eye_center_y = (eye_r[1] + eye_l[1]) / 2.0
        pitch_offset = (nose[1] - eye_center_y) / max(1.0, float(h))

        # 3. Check eye closure
        eyes_closed = self._analyze_eye_closure(frame, eye_r, eye_l)

        # Decision Logic
        if eyes_closed:
            status = "WARNING: EYES CLOSED / DROWSY"
            alert_code = "EYES_CLOSED"
            color = (50, 50, 240) # Red
            self._log_distraction("eyes_closed", "Eyes closed or drowsiness detected")
        elif yaw_offset > 0.42:
            status = "WARNING: HEAD TURNED AWAY"
            alert_code = "TURNED_AWAY"
            color = (0, 165, 255) # Orange
            self._log_distraction("turned_away", "Head turned away from screen")
        elif pitch_offset > 0.38 or (y + h) > (frame_h * 0.95):
            status = "WARNING: LOOKING DOWN (MOBILE/DEVICE)"
            alert_code = "LOOKING_DOWN"
            color = (0, 200, 255) # Yellow
            self._log_distraction("looking_down_mobile", "Looking down or mobile phone use detected")
        else:
            status = "UPRIGHT FOCUS"
            alert_code = "NORMAL"
            color = (99, 179, 241) # Light blue

        return (x, y, w, h), status, alert_code, color

    def generate_mjpeg_frames(self):
        """Generator yielding MJPEG multipart frame byte chunks for HTTP streaming."""
        while True:
            if not self.is_active or self.cap is None:
                time.sleep(0.2)
                continue

            with self.lock:
                if not self.cap.isOpened():
                    break
                success, frame = self.cap.read()

            if not success or frame is None:
                time.sleep(0.05)
                continue

            try:
                now = time.time()

                if self._detector_mode == "yunet" and self.face_detector is not None:
                    h, w = frame.shape[:2]
                    self.face_detector.setInputSize((w, h))
                    _, detections = self.face_detector.detect(frame)

                    if detections is not None and len(detections) > 0:
                        self.last_face_detected = True
                        self.away_start_time = None
                        
                        # Analyze primary face (largest bbox)
                        best_det = max(detections, key=lambda d: d[2] * d[3])
                        bbox, posture_text, alert_code, color = self._analyze_yunet_detection(frame, best_det)
                        
                        self.last_posture = posture_text
                        self.current_alert = alert_code

                        # Draw overlay
                        bx, by, bw, bh = bbox
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), color, 2)
                        cv2.putText(
                            frame, posture_text,
                            (bx, max(by - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            color, 2, cv2.LINE_AA
                        )

                        # Check if multiple faces present (possible phone/second person distraction)
                        if len(detections) > 1:
                            cv2.putText(frame, "MULTIPLE PEOPLE DETECTED", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    else:
                        self.last_face_detected = False
                        if self.away_start_time is None:
                            self.away_start_time = now
                        
                        away_dur = now - self.away_start_time
                        if away_dur > 2.0:
                            self.last_posture = "WARNING: AWAY FROM SCREEN"
                            self.current_alert = "AWAY_FROM_SCREEN"
                            self._log_distraction("away_from_screen", "User turned away or stepped out of camera view")
                            cv2.putText(frame, "⚠ AWAY FROM SCREEN / TURNED AWAY", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        else:
                            self.last_posture = "SEARCHING FOR FACE..."
                            self.current_alert = "SEARCHING"

                elif self._detector_mode == "haar" and self.face_detector is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_detector.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
                    if len(faces) > 0:
                        self.last_face_detected = True
                        self.last_posture = "UPRIGHT FOCUS"
                        self.current_alert = "NORMAL"
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (99, 179, 241), 2)
                    else:
                        self.last_face_detected = False
                        self.last_posture = "WARNING: AWAY FROM SCREEN"
                        self.current_alert = "AWAY_FROM_SCREEN"
                        self._log_distraction("away_from_screen", "No face detected in frame")

                else:
                    self.last_face_detected = True
                    self.last_posture = "VISION COMPANION ACTIVE"
                    self.current_alert = "NORMAL"

                # Encode frame to JPEG
                _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame_bytes
                    + b"\r\n"
                )

            except Exception as e:
                print(f"[WARN] Frame processing error: {e}")
                time.sleep(0.1)


# Singleton instance
camera_manager = CameraFeedManager()
