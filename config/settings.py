import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"

# Ensure data directories exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Ollama LLM Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Sensor & AI Timing Settings
DEFAULT_SENSOR_POLL_INTERVAL_SEC = 2.0
AI_COACHING_INTERVAL_SEC = 30.0  # Configurable interval for periodic AI analysis

# Non-Medical Disclaimer Banner
DISCLAIMER_TEXT = (
    "DISCLAIMER: This system is an AI Study-Focus Companion for academic productivity. "
    "It is NOT a medical device and does NOT perform medical diagnosis, health monitoring, "
    "or clinical advice. All heart-rate readings are simulated for focus pacing."
)
