# FlowMate - AI Study-Focus & IoT Telemetry Assistant

FlowMate is an AI-powered academic study and focus assistant designed to track study pacing using hardware sensor telemetry (ESP32 MAX30102 or stateful simulator) and provide intelligent focus coaching via local Ollama LLM (`llama3.2:3b`).

> **⚠️ NON-MEDICAL DISCLAIMER**  
> This project is purely an academic focus companion for study productivity. It is **NOT** a medical device and does **NOT** perform medical diagnosis, health evaluation, or clinical stress analysis. All heart rate metrics are simulated or used solely for study pacing self-regulation.

---

## Architecture Overview

- **Web REST API & Server (`app.py`)**: Flask web server exposing REST endpoints for real-time telemetry streaming, session lifecycle control, study planning, AI coaching chat, progress analytics, and faculty mentoring.
- **Frontend SPA (`templates/`, `static/`)**: Modern dark glassmorphism web interface with Chart.js telemetry visualization, responsive mobile layout, and 10 main portals.
- **Sensors (`sensors/`)**: Modular hardware abstraction architecture (SIMULATION, HARDWARE, AUTO).
  - `sensors/simulated.py`: Stateful MAX30102 simulator supporting study profiles (`RESTING_FOCUS`, `DEEP_STUDY`, `INTENSE_PROBLEM_SOLVING`, `FATIGUE_SLUMP`, `HIGH_STRESS_ANXIETY`, `DISTRACTED`).
  - `sensors/ble_esp32.py`: Hardware stub for ESP32 Bluetooth BLE MAX30102 sensor.
  - `sensors/camera.py`: Vision processing placeholder.
- **AI Backend (`ai/`)**:
  - `ai/ollama_client.py`: API client for local Ollama server using model `llama3.2:3b`.
  - `ai/prompts.py`: Non-medical coaching system prompts with strict guardrails.
- **Core Orchestrator (`core/`)**:
  - `core/assistant.py`: Session management, statistics calculation, and JSON export to `data/sessions/`.

---

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install & Pull Ollama Model** (if using AI Coaching):
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Launch the Web Dashboard**:
   ```bash
   python app.py
   ```
   Open your browser to: **`http://127.0.0.1:5000`**

4. **Terminal CLI Application** (Alternative):
   ```bash
   python main.py
   ```

---

## Project Structure

```
FlowMate/
├── ai/                      # Ollama client and focus coaching prompts
├── config/                  # Configuration settings & disclaimer text
├── core/                    # Core assistant orchestrator & statistics logic
├── sensors/                 # Sensor hardware abstraction & simulation engine
├── templates/
│   └── index.html           # Single Page Application HTML shell
├── static/
│   ├── css/
│   │   └── style.css        # Dark glassmorphism responsive stylesheet
│   └── js/
│       └── app.js           # SPA controller & Chart.js telemetry logic
├── data/
│   └── sessions/            # Saved study session JSON logs
├── app.py                   # Flask REST API web server
├── main.py                  # Terminal CLI application
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```
