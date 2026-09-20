# AI Study-Focus Assistant

An AI-powered academic study and focus assistant designed to track study pacing using heart-rate metrics and provide intelligent focus coaching via local Ollama LLM (`llama3.2:3b`).

> **⚠️ NON-MEDICAL DISCLAIMER**  
> This project is purely an academic focus companion for study productivity. It is **NOT** a medical device and does **NOT** perform medical diagnosis, health evaluation, or clinical stress analysis. All heart rate metrics are simulated or used solely for study pacing.

---

## Architecture Overview

- **Sensors (`sensors/`)**: Modular hardware abstraction using Abstract Base Classes.
  - `sensors/simulated.py`: Simulated MAX30102 heart rate sensor with configurable study states (`RESTING_FOCUS`, `DEEP_STUDY`, `INTENSE_PROBLEM_SOLVING`).
  - `sensors/ble_esp32.py`: Hardware stub for future ESP32 Bluetooth BLE MAX30102 sensor.
  - `sensors/camera.py`: Minimal vision placeholder.
- **AI Backend (`ai/`)**:
  - `ai/ollama_client.py`: Client for local Ollama server using default model `llama3.2:3b`.
  - `ai/prompts.py`: Focus coaching prompts with strict non-medical guardrails.
- **Core Orchestrator (`core/`)**:
  - `core/assistant.py`: Session management, reading logs, and JSON export to `data/sessions/`.

---

## Setup & Running

1. **Install Ollama** (if not already installed):
   Download from [ollama.com](https://ollama.com) and run:
   ```bash
   ollama pull llama3.2:3b
   ```

2. **Run the Assistant**:
   ```bash
   python main.py
   ```

---

## Project File Structure

```
.
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration defaults & non-medical banner text
├── sensors/
│   ├── __init__.py
│   ├── base.py              # BaseHeartRateSensor ABC & HeartRateReading dataclass
│   ├── simulated.py         # Simulated MAX30102 sensor with synthetic data
│   ├── ble_esp32.py         # Hardware placeholder for ESP32 Bluetooth BLE
│   └── camera.py            # Minimal placeholder for vision processing
├── ai/
│   ├── __init__.py
│   ├── ollama_client.py     # Ollama API client (llama3.2:3b default)
│   └── prompts.py           # Non-medical coaching system prompts
├── core/
│   ├── __init__.py
│   └── assistant.py         # Core StudyAssistant coordinator
├── data/
│   └── sessions/            # Saved study session JSON logs
├── main.py                  # Terminal CLI application
├── requirements.txt         # Dependencies
└── README.md                # Project documentation
```
