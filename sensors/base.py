import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class HeartRateReading:
    """Dataclass encapsulating a heart rate measurement reading."""
    bpm: float
    timestamp: float
    is_simulated: bool
    condition_label: str
    device_name: str

    def __str__(self) -> str:
        sim_tag = "[SIMULATED]" if self.is_simulated else "[REAL HARDWARE]"
        return (
            f"{sim_tag} Device: {self.device_name} | "
            f"BPM: {self.bpm:.1f} | Condition: {self.condition_label} | "
            f"Time: {time.strftime('%H:%M:%S', time.localtime(self.timestamp))}"
        )


class BaseHeartRateSensor(ABC):
    """
    Abstract Base Class for heart rate sensors.
    
    Allows seamless swapping between simulated sensors and real hardware
    (such as an ESP32 + MAX30102 over Bluetooth BLE).
    """

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the sensor hardware or simulator."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the sensor."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the sensor is active and connected."""
        pass

    def get_device_name(self) -> str:
        """Return human-readable device name."""
        return getattr(self, "_device_name", "Heart Rate Sensor")

    @abstractmethod
    def get_reading(self) -> Optional[HeartRateReading]:
        """Fetch the latest heart rate reading."""
        pass
