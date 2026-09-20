import time
from typing import List, Optional
from dataclasses import dataclass
from sensors.base import HeartRateReading

@dataclass
class SessionStatistics:
    latest_bpm: Optional[float]
    average_bpm: Optional[float]
    min_bpm: Optional[float]
    max_bpm: Optional[float]
    sample_count: int
    delta_latest_vs_previous: Optional[float]
    delta_latest_vs_average: Optional[float]
    duration_seconds: float
    recent_trend: str

def calculate_session_statistics(readings: List[HeartRateReading]) -> SessionStatistics:
    """
    Calculate modular session statistics from a list of heart rate readings.
    Works identically for simulated and real hardware data.
    Does NOT interpret these statistics medically.
    """
    sample_count = len(readings)
    
    if sample_count == 0:
        return SessionStatistics(
            latest_bpm=None,
            average_bpm=None,
            min_bpm=None,
            max_bpm=None,
            sample_count=0,
            delta_latest_vs_previous=None,
            delta_latest_vs_average=None,
            duration_seconds=0.0,
            recent_trend="Information unavailable"
        )
        
    latest_bpm = readings[-1].bpm
    all_bpms = [r.bpm for r in readings]
    
    average_bpm = sum(all_bpms) / sample_count
    min_bpm = min(all_bpms)
    max_bpm = max(all_bpms)
    
    duration_seconds = readings[-1].timestamp - readings[0].timestamp
    
    delta_prev = None
    if sample_count >= 2:
        delta_prev = latest_bpm - readings[-2].bpm
        
    delta_avg = latest_bpm - average_bpm
    
    # Simple recent trend calculation (based on last 3 readings if available)
    recent_trend = "STABLE"
    if sample_count >= 3:
        recent_slice = [r.bpm for r in readings[-3:]]
        diff1 = recent_slice[1] - recent_slice[0]
        diff2 = recent_slice[2] - recent_slice[1]
        
        # If both recent steps moved in the same direction beyond a minimal noise threshold
        noise_threshold = 0.5
        if diff1 > noise_threshold and diff2 > noise_threshold:
            recent_trend = "INCREASING"
        elif diff1 < -noise_threshold and diff2 < -noise_threshold:
            recent_trend = "DECREASING"
    
    return SessionStatistics(
        latest_bpm=latest_bpm,
        average_bpm=average_bpm,
        min_bpm=min_bpm,
        max_bpm=max_bpm,
        sample_count=sample_count,
        delta_latest_vs_previous=delta_prev,
        delta_latest_vs_average=delta_avg,
        duration_seconds=duration_seconds,
        recent_trend=recent_trend
    )
