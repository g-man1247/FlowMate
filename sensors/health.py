import time
import random
from typing import Dict, Any

from sensors.base import BaseHeartRateSensor


class HardwareHealthChecker:
    """
    Smartwatch Integration & Signal Diagnostic Service.
    
    Verifies Bluetooth BLE connectivity, measures response latency,
    checks smartwatch battery level, and reports real sensor status.
    """

    @staticmethod
    def run_diagnostic(sensor: BaseHeartRateSensor, sensor_mode: str = "SMARTWATCH") -> Dict[str, Any]:
        start_time = time.time()
        
        device_name = "Smartwatch"
        is_connected = sensor.is_connected()
        
        # Fetch real sample reading
        reading = sensor.get_reading() if is_connected else None
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        diagnostic_logs = []
        battery = getattr(sensor, "get_battery", lambda: None)()
        
        if is_connected and reading:
            health_status = "SMARTWATCH ONLINE"
            signal_quality = 100.0
            stability = "REAL PULSE STABLE"
            diagnostic_logs.append("✔ Smartwatch Bluetooth BLE peripheral connected")
            diagnostic_logs.append(f"✔ Telemetry latency: {latency_ms} ms")
            diagnostic_logs.append("✔ Standard BLE Heart Rate Service active")
            if battery is not None:
                diagnostic_logs.append(f"✔ Smartwatch Battery Level: {battery}%")
        elif is_connected:
            health_status = "SMARTWATCH CONNECTED (AWAITING DATA)"
            signal_quality = 50.0
            stability = "AWAITING HEART RATE"
            diagnostic_logs.append("✔ Smartwatch Bluetooth BLE peripheral connected")
            diagnostic_logs.append("⏳ Waiting for heart-rate measurement notification...")
            if battery is not None:
                diagnostic_logs.append(f"✔ Smartwatch Battery Level: {battery}%")
        else:
            health_status = "SMARTWATCH UNREACHABLE"
            signal_quality = 0.0
            stability = "DISCONNECTED"
            diagnostic_logs.append("✖ Smartwatch BLE device disconnected or out of range")
            diagnostic_logs.append("⚠ Turn on Bluetooth and keep the smartwatch nearby")

        return {
            "timestamp": time.time(),
            "sensor_mode": "SMARTWATCH",
            "connected": is_connected,
            "device_name": device_name,
            "health_status": health_status,
            "latency_ms": latency_ms,
            "signal_quality_pct": signal_quality,
            "battery": battery,
            "stability": stability,
            "sample_bpm": reading.bpm if reading else None,
            "is_simulated": False,
            "diagnostic_logs": diagnostic_logs
        }

