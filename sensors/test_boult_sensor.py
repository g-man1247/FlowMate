import sys
import time

# Ensure stdout handles UTF-8 on Windows command prompts safely
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sensors.boult_sensor import BoultHeartRateSensor


def main():
    print("=" * 60, flush=True)
    print("FLOWMATE - BOULT SENSOR TEST", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    sensor = BoultHeartRateSensor()

    print("Connecting to Boult Watch SH...", flush=True)

    connected = sensor.connect()

    if not connected:
        print("[ERROR] Could not connect to Boult Watch SH.", flush=True)
        print("Ensure watch screen is awake and Bluetooth is enabled on host.", flush=True)
        return

    print(f"[OK] Connected! Device: {sensor.get_device_name()}", flush=True)
    print(f"[STATUS] is_connected(): {sensor.is_connected()}", flush=True)

    battery = sensor.get_battery()
    if battery is not None:
        print(f"[BATTERY] Initial Level: {battery}%", flush=True)

    print("\nListening for real heart-rate notifications...", flush=True)
    print("Press Ctrl+C to exit.\n", flush=True)

    try:
        readings_received = 0
        while True:
            reading = sensor.get_reading()

            if reading:
                readings_received += 1
                bat = sensor.get_battery()
                bat_str = f" | Battery: {bat}%" if bat is not None else ""
                print(f"[READING #{readings_received}] {reading}{bat_str}", flush=True)
            else:
                print("[WAIT] Waiting for heart-rate notification packet...", flush=True)

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received. Stopping test...", flush=True)

    finally:
        print("[INFO] Disconnecting sensor...", flush=True)
        sensor.disconnect()
        print(f"[STATUS] is_connected(): {sensor.is_connected()}", flush=True)
        print("[OK] Test finished cleanly.", flush=True)


if __name__ == "__main__":
    main()