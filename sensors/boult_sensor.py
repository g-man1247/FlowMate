import asyncio
import sys
import time
import threading
from typing import Optional, Union

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError, BleakDeviceNotFoundError

from .base import BaseHeartRateSensor, HeartRateReading


# Standard BLE Heart Rate Measurement characteristic
HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Standard BLE Battery Level characteristic
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

DEFAULT_WATCH_NAME = "Boult Watch SH"
OBSERVED_MAC_ADDRESS = "3A:E3:6A:D3:09:D5"


class BoultHeartRateSensor(BaseHeartRateSensor):
    """
    Real BLE heart-rate sensor integrating the Boult Watch SH (firmware MOY-V904-2.0.0).
    Communicates asynchronously via Bleak, bridged safely to the synchronous
    FlowMate BaseHeartRateSensor interface.
    """

    def __init__(
        self,
        target_name: str = DEFAULT_WATCH_NAME,
        target_address: Optional[str] = OBSERVED_MAC_ADDRESS,
        auto_reconnect: bool = True
    ):
        self._target_name = target_name
        self._target_address = target_address
        self._device_name = target_name
        self.auto_reconnect = auto_reconnect

        self.client: Optional[BleakClient] = None
        self._lock = threading.Lock()

        self._connected = False
        self._latest_bpm: Optional[float] = None
        self._latest_timestamp: Optional[float] = None
        self._battery: Optional[int] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ---------------------------------------------------------
    # SYNCHRONOUS INTERFACE BRIDGE
    # ---------------------------------------------------------

    def connect(self) -> bool:
        """
        Connect to the Boult Watch.
        Synchronous interface matching BaseHeartRateSensor.
        Starts a background daemon thread running the asyncio BLE event loop.
        """
        with self._lock:
            if self._connected:
                return True

        self._stop_event.clear()

        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._run_ble_loop,
                daemon=True,
                name="BoultBLEThread"
            )
            self._thread.start()

        # Wait up to 15 seconds for initial BLE connection & handshake
        start_wait = time.time()
        while time.time() - start_wait < 15.0:
            with self._lock:
                if self._connected:
                    return True
            if self._stop_event.is_set():
                break
            time.sleep(0.1)

        return self.is_connected()

    def disconnect(self) -> None:
        """
        Cleanly stop notifications, disconnect BLE client, and stop background loop.
        """
        self._stop_event.set()

        if self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._disconnect_async(),
                    self._loop
                )
                future.result(timeout=3.0)
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

        with self._lock:
            self._connected = False
            self.client = None

        print("[INFO] Boult Watch sensor disconnected cleanly.")

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def get_device_name(self) -> str:
        with self._lock:
            return self._device_name

    def get_battery(self) -> Optional[int]:
        with self._lock:
            return self._battery

    # ---------------------------------------------------------
    # BACKGROUND ASYNCIO BLE LOOP
    # ---------------------------------------------------------

    def _run_ble_loop(self):
        """Run background asyncio event loop for BLE operations."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            while not self._stop_event.is_set():
                try:
                    self._loop.run_until_complete(self._ble_main())
                except Exception as e:
                    print(f"[WARN] Boult BLE session error: {e}")

                with self._lock:
                    self._connected = False

                if not self.auto_reconnect or self._stop_event.is_set():
                    break

                print("[INFO] Connection closed. Reconnecting in 3 seconds...")
                for _ in range(30):
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.1)
        finally:
            with self._lock:
                self._connected = False
            try:
                self._loop.close()
            except Exception:
                pass

    async def _ble_main(self):
        """Discover watch, connect, subscribe to GATT characteristics, and hold connection."""
        print(f"[INFO] Scanning for {self._target_name}...")

        device_target = await self._discover_device()

        if device_target is None:
            print(f"[WARN] {self._target_name} not found during scan.")
            return

        if isinstance(device_target, BLEDevice):
            device_desc = f"{device_target.name} [{device_target.address}]"
            with self._lock:
                self._device_name = device_target.name or self._target_name
        else:
            device_desc = f"Address {device_target}"
            with self._lock:
                self._device_name = self._target_name

        print(f"[OK] Watch target found: {device_desc}")
        print("[INFO] Connecting to Boult Watch...")

        self.client = BleakClient(
            device_target,
            disconnected_callback=self._on_disconnect
        )

        try:
            await self.client.connect()
        except BleakDeviceNotFoundError:
            print(f"[WARN] Device {device_desc} not in range or asleep.")
            return
        except BleakError as e:
            print(f"[WARN] BLE Connection error: {e}")
            return
        except Exception as e:
            print(f"[WARN] Unexpected connection error: {e}")
            return

        if not self.client.is_connected:
            print("[WARN] Connection failed.")
            return

        with self._lock:
            self._connected = True

        print("[OK] Connected to Boult Watch.")

        # Subscribe to Heart Rate characteristic
        try:
            await self.client.start_notify(
                HEART_RATE_UUID,
                self._heart_rate_callback
            )
            print("[OK] Heart-rate notifications enabled.")
        except Exception as e:
            print(f"[ERROR] Failed to enable heart-rate notifications: {e}")
            with self._lock:
                self._connected = False
            await self._disconnect_async()
            return

        # Subscribe to & read Battery characteristic (optional feature, does not crash HR)
        try:
            await self.client.start_notify(
                BATTERY_UUID,
                self._battery_callback
            )
            print("[OK] Battery notifications enabled.")
        except Exception as e:
            print(f"[INFO] Battery notification subscription skipped: {e}")

        try:
            battery_bytes = await self.client.read_gatt_char(BATTERY_UUID)
            if battery_bytes and len(battery_bytes) >= 1:
                bat_val = int(battery_bytes[0])
                with self._lock:
                    self._battery = bat_val
                print(f"[OK] Initial Battery level: {bat_val}%")
        except Exception as e:
            print(f"[INFO] Battery level read skipped: {e}")

        # Keep connection session alive
        while not self._stop_event.is_set():
            if not self.client or not self.client.is_connected:
                print("[WARN] Watch connection lost in loop.")
                break
            await asyncio.sleep(0.5)

        # Cleanup BLE notifications & client on disconnect
        await self._disconnect_async()

    async def _discover_device(self) -> Optional[Union[BLEDevice, str]]:
        """
        Scan for device by target name primarily,
        falling back to target MAC address.
        """
        target_name_lower = self._target_name.lower()
        target_addr_upper = self._target_address.upper() if self._target_address else None

        for attempt in range(2):
            if self._stop_event.is_set():
                return None
            try:
                devices = await BleakScanner.discover(timeout=4.0)

                # 1. Primary match: device name contains "Boult Watch SH" or "Boult"
                for dev in devices:
                    dev_name = dev.name or ""
                    if target_name_lower in dev_name.lower() or "boult" in dev_name.lower():
                        return dev

                # 2. Secondary match: MAC address in discovered devices list
                if target_addr_upper:
                    for dev in devices:
                        if dev.address.upper() == target_addr_upper:
                            return dev
            except Exception as e:
                print(f"[WARN] Bleak scan attempt error: {e}")

        # 3. Fallback to direct address string connection attempt
        if target_addr_upper:
            return self._target_address

        return None

    async def _disconnect_async(self):
        """Internal async disconnect helper."""
        if self.client is None:
            return

        try:
            if self.client.is_connected:
                try:
                    await self.client.stop_notify(HEART_RATE_UUID)
                except Exception:
                    pass
                try:
                    await self.client.stop_notify(BATTERY_UUID)
                except Exception:
                    pass
                await self.client.disconnect()
        except Exception as e:
            print(f"[INFO] Disconnect cleanup warning: {e}")
        finally:
            with self._lock:
                self._connected = False
                self.client = None

    # ---------------------------------------------------------
    # CALLBACKS & PACKET PARSING
    # ---------------------------------------------------------

    def _heart_rate_callback(self, sender, data: bytearray):
        """
        Process standard BLE Heart Rate Measurement packets.
        Byte 0: Flags byte
          - Bit 0: 0 = UINT8 heart rate (data[1]), 1 = UINT16 heart rate (data[1:3] little-endian)
        """
        if not data or len(data) < 2:
            return

        try:
            flags = data[0]
            is_uint16 = bool(flags & 0x01)

            if is_uint16:
                if len(data) < 3:
                    return
                bpm = int.from_bytes(data[1:3], byteorder="little")
            else:
                bpm = data[1]

            bpm_val = float(bpm)
            if 30.0 <= bpm_val <= 240.0:
                with self._lock:
                    self._latest_bpm = bpm_val
                    self._latest_timestamp = time.time()
        except Exception as e:
            print(f"[WARN] Heart-rate packet parsing error: {e}")

    def _battery_callback(self, sender, data: bytearray):
        """Process BLE Battery Level notifications."""
        if data and len(data) >= 1:
            try:
                bat_val = int(data[0])
                with self._lock:
                    self._battery = bat_val
            except Exception as e:
                print(f"[WARN] Battery packet parsing error: {e}")

    def _on_disconnect(self, client):
        """Callback invoked by Bleak when device disconnects."""
        print("[WARN] Watch disconnected.")
        with self._lock:
            self._connected = False

    # ---------------------------------------------------------
    # SENSOR READINGS & CONDITION MAPPING
    # ---------------------------------------------------------

    def get_reading(self) -> Optional[HeartRateReading]:
        """Fetch the latest heart rate reading if connected and fresh."""
        with self._lock:
            bpm = self._latest_bpm
            ts = self._latest_timestamp
            dev_name = self._device_name
            is_conn = self._connected

        if not is_conn or bpm is None or ts is None:
            return None

        # Ignore stale readings if no update in the last 15 seconds
        if time.time() - ts > 15.0:
            return None

        condition_label = self._classify_heart_rate(bpm)

        return HeartRateReading(
            bpm=bpm,
            timestamp=ts,
            is_simulated=False,
            condition_label=condition_label,
            device_name=dev_name
        )

    @staticmethod
    def _classify_heart_rate(bpm: float) -> str:
        """
        Map BPM to FlowMate condition label (non-medical academic state).
        Matches condition keys expected by StudyAssistant and app focus calculation.
        """
        if bpm < 60.0:
            return "FATIGUE_SLUMP"
        elif bpm < 75.0:
            return "RESTING_FOCUS"
        elif bpm < 90.0:
            return "DEEP_STUDY"
        elif bpm < 105.0:
            return "INTENSE_PROBLEM_SOLVING"
        else:
            return "HIGH_STRESS_ANXIETY"