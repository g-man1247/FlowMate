import random
import time
from typing import Dict, Optional
from sensors.base import BaseHeartRateSensor, HeartRateReading


class SimulatedHeartRateSensor(BaseHeartRateSensor):
    """
    Simulated heart rate sensor for development and testing.
    
    Generates synthetic heart rate readings under different study conditions.
    Uses a stateful random walk (momentum + noise) to simulate realistic gradual 
    changes in heart rate, rather than erratic random jumps.
    Readings are explicitly flagged as simulated (`is_simulated=True`).
    """

    # Predefined simulated condition profiles (base BPM range)
    CONDITIONS: Dict[str, tuple[float, float]] = {
        "RESTING_FOCUS": (62.0, 72.0),
        "DEEP_STUDY": (70.0, 82.0),
        "INTENSE_PROBLEM_SOLVING": (83.0, 98.0),
        "FATIGUE_SLUMP": (55.0, 64.0),
        "HIGH_STRESS_ANXIETY": (95.0, 115.0),
        "DISTRACTED": (68.0, 88.0),
    }

    def __init__(self, initial_condition: str = "DEEP_STUDY", seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            
        self._connected = False
        self._current_condition = initial_condition if initial_condition in self.CONDITIONS else "DEEP_STUDY"
        self._device_name = "Simulated MAX30102"
        
        # Stateful tracking for gradual movement
        self._current_bpm: Optional[float] = None
        self._absolute_min = 50.0
        self._absolute_max = 130.0

    def connect(self) -> bool:
        """Connect to the simulated sensor."""
        self._connected = True
        
        # Initialize starting BPM based on current condition median
        min_bpm, max_bpm = self.CONDITIONS[self._current_condition]
        self._current_bpm = (min_bpm + max_bpm) / 2.0
        return True

    def disconnect(self) -> None:
        """Disconnect from the simulated sensor."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check connection state."""
        return self._connected

    def set_condition(self, condition_name: str) -> bool:
        """Change the active simulated study condition."""
        if condition_name in self.CONDITIONS:
            self._current_condition = condition_name
            return True
        return False

    def get_available_conditions(self) -> list[str]:
        """Return list of supported simulated conditions."""
        return list(self.CONDITIONS.keys())

    def get_reading(self) -> Optional[HeartRateReading]:
        """
        Generate a simulated heart rate reading using gradual momentum.
        Moves slowly toward the condition's median target with small noise.
        """
        if not self._connected or self._current_bpm is None:
            return None

        # Determine target center for the current condition
        min_bpm, max_bpm = self.CONDITIONS[self._current_condition]
        target_bpm = (min_bpm + max_bpm) / 2.0
        
        # Drift toward target (10% closure per tick)
        drift = (target_bpm - self._current_bpm) * 0.1
        
        # Add small random noise (standard deviation of 1.2 BPM)
        noise = random.gauss(0.0, 1.2)
        
        # Apply changes and clamp to absolute physiological bounds
        new_bpm = self._current_bpm + drift + noise
        self._current_bpm = max(self._absolute_min, min(self._absolute_max, new_bpm))

        return HeartRateReading(
            bpm=round(self._current_bpm, 1),
            timestamp=time.time(),
            is_simulated=True,
            condition_label=self._current_condition,
            device_name=self._device_name,
        )
