import time
from typing import List, Optional, Dict, Any
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
    Works for any sensor implementation.
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

    recent_trend = "STABLE"
    if sample_count >= 3:
        recent_slice = [r.bpm for r in readings[-3:]]
        diff1 = recent_slice[1] - recent_slice[0]
        diff2 = recent_slice[2] - recent_slice[1]

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


def calculate_stress_estimate(readings: List[HeartRateReading]) -> Dict[str, Any]:
    """
    Transparent, non-medical stress estimation based strictly on real smartwatch heart-rate data.
    Requires at least 3 valid readings to establish a baseline.
    Never fabricates physiological measurements.

    Stress tiers (non-medical academic context only):
      LOW      — resting / calm state
      NORMAL   — active cognitive engagement, expected during study
      ELEVATED — above-average sustained HR, consider a short break
      HIGH     — significantly elevated HR, break recommended
    """
    real_readings = [r for r in readings if not r.is_simulated]

    if len(real_readings) < 3:
        return {
            "level": "Collecting data...",
            "score_pct": 0,
            "explanation": "Awaiting at least 3 real smartwatch heart-rate samples.",
            "is_valid": False
        }

    recent = real_readings[-10:]
    latest_bpm = recent[-1].bpm
    rolling_avg = sum(r.bpm for r in recent) / len(recent)
    delta = latest_bpm - rolling_avg

    # Base scale: 55 BPM → 10%, 100 BPM → 85%
    raw_score = ((rolling_avg - 55.0) / 45.0) * 75.0 + 10.0

    # Short-term surge penalty (sustained spike above rolling avg)
    if delta > 3.0:
        raw_score += (delta - 3.0) * 2.0

    stress_pct = max(5, min(95, int(raw_score)))

    if stress_pct < 30 or latest_bpm < 68.0:
        level = "LOW"
        explanation = f"Resting heart rate (Avg: {rolling_avg:.1f} BPM). Calm, relaxed state."
    elif stress_pct < 55 or latest_bpm < 85.0:
        level = "NORMAL"
        explanation = f"Active study engagement (Avg: {rolling_avg:.1f} BPM, Latest: {latest_bpm:.1f} BPM). Normal cognitive load."
    elif stress_pct < 75 or latest_bpm < 100.0:
        level = "ELEVATED"
        explanation = f"Above-average heart rate (Latest: {latest_bpm:.1f} BPM vs Avg: {rolling_avg:.1f} BPM). Consider a short break."
    else:
        level = "HIGH"
        explanation = f"Significantly elevated heart rate (Latest: {latest_bpm:.1f} BPM vs Avg: {rolling_avg:.1f} BPM). Break recommended."

    return {
        "level": level,
        "score_pct": stress_pct,
        "explanation": explanation,
        "latest_bpm": latest_bpm,
        "rolling_avg": round(rolling_avg, 1),
        "is_valid": True
    }
