"""
Feature extraction and personal baseline computation for WardPulse.

Calculates personal vitals baselines using robust statistics (median and MAD),
condition-based priors for sparse history, trend analysis, shock index, and vital ages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
from typing import Dict, List, Optional

from shared.schemas import Condition, EngineConfig, Patient, VitalName, VitalsReading


# Condition-based clinical priors (default population reference baselines)
CONDITION_PRIORS: Dict[str, Dict[VitalName, float]] = {
    "copd": {
        VitalName.HR: 80.0,
        VitalName.SBP: 125.0,
        VitalName.DBP: 78.0,
        VitalName.RR: 21.5,
        VitalName.SPO2: 91.0,
        VitalName.TEMP: 36.8,
    },
    "post_op": {
        VitalName.HR: 76.0,
        VitalName.SBP: 120.0,
        VitalName.DBP: 76.0,
        VitalName.RR: 14.5,
        VitalName.SPO2: 97.5,
        VitalName.TEMP: 36.9,
    },
    "cardiac": {
        VitalName.HR: 96.0,
        VitalName.SBP: 148.0,
        VitalName.DBP: 90.0,
        VitalName.RR: 17.0,
        VitalName.SPO2: 96.0,
        VitalName.TEMP: 36.7,
    },
    "general": {
        VitalName.HR: 72.0,
        VitalName.SBP: 120.0,
        VitalName.DBP: 76.0,
        VitalName.RR: 15.0,
        VitalName.SPO2: 98.0,
        VitalName.TEMP: 36.7,
    },
}

# Floor spread to prevent zero-division on stable repeated readings
FLOOR_SPREAD: Dict[VitalName, float] = {
    VitalName.HR: 5.0,
    VitalName.SBP: 6.0,
    VitalName.DBP: 5.0,
    VitalName.RR: 1.5,
    VitalName.SPO2: 1.0,
    VitalName.TEMP: 0.2,
}


def get_condition_prior(patient: Patient) -> Dict[VitalName, float]:
    """Retrieve condition-specific prior vitals based on patient conditions."""
    if Condition.COPD in patient.conditions:
        return CONDITION_PRIORS["copd"]
    if Condition.POST_OP in patient.conditions:
        return CONDITION_PRIORS["post_op"]
    if Condition.CARDIAC in patient.conditions:
        return CONDITION_PRIORS["cardiac"]
    return CONDITION_PRIORS["general"]


@dataclass
class VitalBaseline:
    """Baseline metrics for a single vital sign."""
    vital: VitalName
    current_value: Optional[float]
    effective_baseline: float
    spread: float
    z_score: float                     # signed deviation (positive = above baseline)
    trend_per_hour: Optional[float]    # delta per hour
    age_hours: Optional[float]
    n_readings_used: int


@dataclass
class PatientFeatures:
    """Extracted feature vector for a patient at evaluation time."""
    patient_id: int
    bed: int
    evaluated_at: datetime
    baselines: Dict[VitalName, VitalBaseline]
    shock_index: Optional[float]       # HR / SBP
    hours_since_last_vitals: Optional[float]
    latest_reading: Optional[VitalsReading]
    prior_reading: Optional[VitalsReading]
    reasons: List[str] = field(default_factory=list)


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _mad(values: List[float], med: float) -> float:
    """Median Absolute Deviation (MAD)."""
    devs = [abs(v - med) for v in values]
    return _median(devs)


def extract_features(
    patient: Patient,
    readings: List[VitalsReading],
    now: datetime,
    config: EngineConfig,
) -> PatientFeatures:
    """Extract features, robust baselines, trends, and shock index for a patient."""
    prior = get_condition_prior(patient)

    if not readings:
        baselines: Dict[VitalName, VitalBaseline] = {}
        for vital in VitalName:
            baselines[vital] = VitalBaseline(
                vital=vital,
                current_value=None,
                effective_baseline=prior[vital],
                spread=FLOOR_SPREAD[vital],
                z_score=0.0,
                trend_per_hour=None,
                age_hours=None,
                n_readings_used=0,
            )
        return PatientFeatures(
            patient_id=patient.id,
            bed=patient.bed,
            evaluated_at=now,
            baselines=baselines,
            shock_index=None,
            hours_since_last_vitals=None,
            latest_reading=None,
            prior_reading=None,
            reasons=["No vitals recorded"],
        )

    # Sort chronologically
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    latest_reading = sorted_readings[-1]
    prior_reading = sorted_readings[-2] if len(sorted_readings) >= 2 else None

    # Filter baseline history:
    # within baseline_window_hours, excluding latest baseline_exclude_latest reading(s)
    cutoff = now - timedelta(hours=config.baseline_window_hours)
    history_candidates = [r for r in sorted_readings if r.timestamp >= cutoff]

    if len(history_candidates) > config.baseline_exclude_latest:
        baseline_history = history_candidates[:-config.baseline_exclude_latest]
    else:
        baseline_history = []

    baselines = {}
    reasons: List[str] = []

    for vital in VitalName:
        vital_str = vital.value
        current_val = getattr(latest_reading, vital_str, None)
        floor = FLOOR_SPREAD[vital]

        # Collect past measurements for this vital in baseline history
        past_vals = [
            getattr(r, vital_str)
            for r in baseline_history
            if getattr(r, vital_str) is not None
        ]
        n_vals = len(past_vals)

        # Robust baseline: median and MAD
        if n_vals > 0:
            obs_median = _median(past_vals)
            obs_mad = _mad(past_vals, obs_median)
            # 1.4826 scale factor converts MAD to normal standard deviation estimate
            spread = max(1.4826 * obs_mad, floor)
        else:
            obs_median = prior[vital]
            spread = floor

        # Blend toward prior if fewer than min_baseline_readings
        if n_vals < config.min_baseline_readings:
            ratio = n_vals / float(config.min_baseline_readings)
            blend_weight = config.prior_blend * (1.0 - ratio)
            effective_base = (1.0 - blend_weight) * obs_median + blend_weight * prior[vital]
        else:
            effective_base = obs_median

        # Find the previous measurement of this vital (before latest_reading)
        prev_vital_val: Optional[float] = None
        prev_vital_time: Optional[datetime] = None
        for r in reversed(sorted_readings[:-1]):
            val = getattr(r, vital_str, None)
            if val is not None:
                prev_vital_val = val
                prev_vital_time = r.timestamp
                break

        # Calculate deviation (z-score) using current value or last recorded measurement
        ref_val = current_val if current_val is not None else prev_vital_val
        if ref_val is not None:
            z = (ref_val - effective_base) / spread
        else:
            z = 0.0

        # Calculate trend per hour
        trend_per_hour: Optional[float] = None
        if current_val is not None and prev_vital_val is not None and prev_vital_time is not None:
            dt_hours = (latest_reading.timestamp - prev_vital_time).total_seconds() / 3600.0
            if dt_hours > 0.05:  # at least 3 minutes apart
                trend_per_hour = round((current_val - prev_vital_val) / dt_hours, 2)

        # Age in hours of the latest measurement of this vital
        vital_time = None
        if current_val is not None:
            vital_time = latest_reading.timestamp
        elif prev_vital_time is not None:
            vital_time = prev_vital_time

        age_hours = (
            (now - vital_time).total_seconds() / 3600.0
            if vital_time is not None else None
        )

        baselines[vital] = VitalBaseline(
            vital=vital,
            current_value=ref_val,
            effective_baseline=round(effective_base, 1),
            spread=round(spread, 2),
            z_score=round(z, 2),
            trend_per_hour=trend_per_hour,
            age_hours=round(age_hours, 1) if age_hours is not None else None,
            n_readings_used=n_vals,
        )

    # Shock index: HR / SBP
    hr_val = getattr(latest_reading, "hr", None)
    sbp_val = getattr(latest_reading, "sbp", None)
    shock_index: Optional[float] = None
    if hr_val is not None and sbp_val is not None and sbp_val > 0:
        shock_index = round(hr_val / sbp_val, 2)

    hours_since_last = (now - latest_reading.timestamp).total_seconds() / 3600.0

    return PatientFeatures(
        patient_id=patient.id,
        bed=patient.bed,
        evaluated_at=now,
        baselines=baselines,
        shock_index=shock_index,
        hours_since_last_vitals=round(hours_since_last, 1),
        latest_reading=latest_reading,
        prior_reading=prior_reading,
        reasons=reasons,
    )
