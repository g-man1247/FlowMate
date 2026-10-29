# FlowMate - Smartwatch BLE Integration & Responsive Web App

FlowMate is an AI-powered academic study and focus assistant that tracks real-time study pacing using **real smartwatch heart-rate telemetry over Bluetooth Low Energy (BLE)** and provides intelligent focus coaching via local Ollama LLM (`llama3.2:3b`).

> **⚠️ NON-MEDICAL DISCLAIMER**  
> FlowMate is purely an academic focus companion for study productivity self-regulation. It is **NOT** a medical device and does **NOT** perform medical diagnosis, clinical health evaluation, or clinical stress analysis.

---

## 1. How to Run FlowMate on Windows

Run the web server using `uv`:

```powershell
uv run python app.py
```

Open your browser on Windows to:
- **`http://127.0.0.1:5000`**

---

## 2. Real Smartwatch BLE Telemetry Architecture

FlowMate uses **100% REAL smartwatch heart-rate data** in production. No simulated or fake heart-rate readings are generated in the application.

```
SMARTWATCH (BLE GATT Notifications)
       ↓ (Bluetooth LE)
WINDOWS COMPUTER (Python Bleak Sensor Layer)
       ↓ (Memory State / Flask REST API)
FLOWMATE BACKEND API (/api/status & /api/sensor/read)
       ↓ (HTTP / Polling every 1 second)
FLOWMATE WEB FRONTEND (Dashboard / Pomodoro Timer / Stress Analysis)
```

---

## 3. How to Enable Bluetooth & Connect the Smartwatch

1. Turn on **Bluetooth** in Windows Settings (`Settings -> Bluetooth & devices -> Bluetooth: ON`).
2. Wake up your smartwatch screen and keep it close to your laptop/computer.
3. FlowMate automatically scans for nearby BLE smartwatches and subscribes to the standard Bluetooth Heart Rate Measurement GATT characteristic (`00002a37-0000-1000-8000-00805f9b34fb`) and Battery Level characteristic (`00002a19-0000-1000-8000-00805f9b34fb`).

---

## 4. How to Test Smartwatch BLE Data

To test smartwatch discovery, connection, and real-time heart-rate notifications directly in the terminal, run:

```powershell
uv run python sensors/test_boult_data.py
```

Expected output when watch is active and on your wrist:
```text
============================================================
FLOWMATE - BOULT DATA TEST
============================================================
Found: Boult Watch SH
Connecting...
✅ Connected!

🔋 Initial Battery: 47%
❤️ Heart-rate notifications enabled.
🔋 Battery notifications enabled.

============================================================
LISTENING FOR DATA
============================================================
[15:20:01] ❤️ Heart Rate: 93 BPM
[15:20:02] ❤️ Heart Rate: 93 BPM
[15:20:03] ❤️ Heart Rate: 90 BPM
[15:20:04] ❤️ Heart Rate: 92 BPM
```

---

## 5. How to Open FlowMate from a Phone on the Same Network

Your Windows PC acts as the BLE host and web server. Phones on the same Wi-Fi/local network can open the FlowMate web interface in any mobile browser (Safari, Chrome, Firefox).

1. Start FlowMate on Windows:
   ```powershell
   uv run python app.py
   ```
2. Note the Network Access URL output in the terminal, for example:
   ```text
   Running web interface at:
     Local Access:   http://127.0.0.1:5000
     Network Access: http://192.168.1.5:5000
   ```
3. On your Android or iPhone browser, visit:
   `http://<laptop-ip-address>:5000` (e.g., `http://192.168.1.5:5000`)
4. The mobile UI is fully responsive with single-column layout, touch-friendly controls, and live heart rate / stress tracking.

---

## 6. Known Smartwatch Control Limitations

> **Documented Limitation:**  
> **Watch screen control is not available through the currently exposed BLE interface.**

- Standard BLE Heart Rate Profile (`0000180d`) provides notify/read operations for heart rate measurements.
- Vendor-specific GATT characteristics do not expose safe, standard write commands for remotely forcing the smartwatch screen to open its internal measurement UI without proprietary mobile app protocol handshakes.
- FlowMate provides a **"Start Heart Rate Measurement"** session trigger in the web UI that listens continuously to live BLE heart-rate notifications from the smartwatch.

---

## 7. Troubleshooting Bluetooth Connection Problems

- **Watch Not Discovered:**
  - Wake up the watch screen.
  - Ensure the watch is not connected exclusively to another mobile app (disconnecting from the phone app frees the BLE GATT server).
  - Bring the watch closer to the Windows computer's Bluetooth receiver.
- **Bluetooth Disabled Error:**
  - Verify Windows Bluetooth is enabled in Action Center or Settings.
- **Disconnected Status in UI:**
  - If the smartwatch goes out of range or sleeps, FlowMate UI displays `Smartwatch Disconnected` and `-- BPM` rather than inventing fake data. Reconnect by waking the watch screen.

---

## Project Structure

```text
FlowMate/
├── ai/                      # Ollama client and focus coaching prompts
├── config/                  # Configuration settings & disclaimer text
├── core/                    # Core assistant orchestrator & statistics logic
├── data/                    # Saved study session JSON logs
├── sensors/                 # Smartwatch BLE sensor integration
│   ├── base.py              # Abstract base class & HeartRateReading dataclass
│   ├── boult_sensor.py      # Production async-to-sync BLE smartwatch sensor
│   ├── boult_watch.py       # Standalone Bleak watch client
│   ├── health.py            # Hardware health & signal diagnostic checker
│   └── test_boult_data.py   # Terminal BLE test runner script
├── static/                  # Responsive CSS & frontend JS
│   ├── css/style.css        # Responsive dark/light theme CSS
│   └── js/app.js            # Frontend telemetry controller & Pomodoro timer
├── templates/
│   └── index.html           # Responsive web app HTML
├── app.py                   # Flask REST API web server
└── README.md                # Documentation
```
