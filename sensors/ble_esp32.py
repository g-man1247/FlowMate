"""
ESP32 Bluetooth (BLE) MAX30102 Sensor Module (Placeholder/Stub).

This module is designed to be implemented when real ESP32 + MAX30102 hardware
is connected over Bluetooth low energy (BLE). It inherits from BaseHeartRateSensor,
ensuring seamless integration without modifying core application logic.
"""

from typing import Optional
from sensors.base import BaseHeartRateSensor, HeartRateReading


class ESP32BluetoothHeartRateSensor(BaseHeartRateSensor):
    """
    Placeholder sensor for ESP32 MAX30102 hardware over Bluetooth BLE.
    Currently acts as a hardware stub until BLE integration is added.
    """

    def __init__(self, ble_address: Optional[str] = None):
        self.ble_address = ble_address or "00:00:00:00:00:00"
        self._connected = False
        self._device_name = "ESP32_MAX30102_BLE"

    def connect(self) -> bool:
        """Attempt connection to ESP32 BLE peripheral."""
        # Hardware BLE connection logic will be implemented here (e.g. using bleak)
        print(f"[BLE STUB] Attempting connection to ESP32 at {self.ble_address}...")
        self._connected = False
        return False

    def disconnect(self) -> None:
        """Disconnect from ESP32 BLE peripheral."""
        self._connected = False
        print("[BLE STUB] Disconnected from ESP32 BLE device.")

    def is_connected(self) -> bool:
        """Check BLE connection state."""
        return self._connected

    def get_reading(self) -> Optional[HeartRateReading]:
        """Fetch heart rate reading from ESP32 MAX30102 hardware."""
        if not self._connected:
            return None
        # Future BLE packet parsing will happen here
        raise NotImplementedError("ESP32 Bluetooth BLE hardware parser is not yet connected.")
