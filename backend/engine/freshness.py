"""
Freshness calculation and measurement schedule evaluation for WardPulse.

Determines next vitals due times based on risk tiers, tracks vital ages,
and flags stale measurements and borderline-and-stale cases.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from shared.schemas import EngineConfig, RiskTier, VitalName, VitalsReading
from engine.features import PatientFeatures


@dataclass
class FreshnessResult:
    """Freshness assessment for a single patient."""
    patient_id: int
    risk_tier: RiskTier
    due_interval_hours: float
    hours_since_last_vitals: Optional[float]
    next_vitals_due: Optional[datetime]
    stale_vitals: List[VitalName]
    is_data_stale: bool
    is_borderline_and_stale: bool


def calculate_freshness(
    patient_id: int,
    risk_tier: RiskTier,
    risk_score: float,
    features: PatientFeatures,
    now: datetime,
    config: EngineConfig,
) -> FreshnessResult:
    """Calculate due intervals, next vitals due timestamp, and staleness flags."""
    # 1. Due interval based on risk tier
    due_interval = config.vitals_due_hours.get(risk_tier, 4.0)
    stale_threshold_hours = due_interval * config.stale_after_factor

    latest_reading = features.latest_reading

    if latest_reading is None:
        return FreshnessResult(
            patient_id=patient_id,
            risk_tier=risk_tier,
            due_interval_hours=due_interval,
            hours_since_last_vitals=None,
            next_vitals_due=now,
            stale_vitals=list(VitalName),
            is_data_stale=True,
            is_borderline_and_stale=False,
        )

    # 2. Hours since last set of vitals
    hours_since_last = (now - latest_reading.timestamp).total_seconds() / 3600.0
    next_due = latest_reading.timestamp + timedelta(hours=due_interval)

    # 3. Check individual vital ages and due intervals
    stale_vitals: List[VitalName] = []
    has_borderline_vital = False

    for vital, baseline in features.baselines.items():
        # If an individual vital exhibits borderline deviation, its due interval is tightened to MEDIUM
        vital_due = due_interval
        if (
            baseline.z_score < -0.5
            or baseline.z_score > 1.2
            or (vital == VitalName.SBP and baseline.current_value is not None and baseline.current_value <= 114.0)
        ):
            vital_due = min(due_interval, config.vitals_due_hours.get(RiskTier.MEDIUM, 4.0))
            has_borderline_vital = True

        vital_stale_thresh = vital_due * config.stale_after_factor
        if baseline.age_hours is None or baseline.age_hours > vital_stale_thresh:
            stale_vitals.append(vital)

    # If the latest overall reading itself is older than threshold, data is stale
    is_data_stale = hours_since_last > stale_threshold_hours or len(stale_vitals) > 0

    # 4. Borderline-and-stale detection
    is_borderline = (
        risk_tier == RiskTier.MEDIUM
        or (0.15 <= risk_score <= (config.tier_high - 0.02))
        or has_borderline_vital
    )
    is_borderline_and_stale = is_borderline and (len(stale_vitals) > 0 or is_data_stale)

    return FreshnessResult(
        patient_id=patient_id,
        risk_tier=risk_tier,
        due_interval_hours=due_interval,
        hours_since_last_vitals=round(hours_since_last, 1),
        next_vitals_due=next_due,
        stale_vitals=stale_vitals,
        is_data_stale=is_data_stale,
        is_borderline_and_stale=is_borderline_and_stale,
    )
