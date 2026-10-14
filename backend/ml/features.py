"""
Feature representation and conversion for WardPulse LightGBM model.

Extracts tabular feature vectors from PatientFeatures, VitalBaseline metrics,
and Patient condition priors matching engine/features.py.
"""

from typing import List, Optional
import numpy as np

from engine.features import PatientFeatures
from shared.schemas import Condition, Patient, VitalName


FEATURE_NAMES: List[str] = [
    # Heart rate
    "hr_value", "hr_zscore", "hr_trend", "hr_age",
    # Systolic blood pressure
    "sbp_value", "sbp_zscore", "sbp_trend", "sbp_age",
    # Diastolic blood pressure
    "dbp_value", "dbp_zscore", "dbp_trend", "dbp_age",
    # Respiratory rate
    "rr_value", "rr_zscore", "rr_trend", "rr_age",
    # Oxygen saturation
    "spo2_value", "spo2_zscore", "spo2_trend", "spo2_age",
    # Temperature
    "temp_value", "temp_zscore", "temp_trend", "temp_age",
    # Aggregate physiological markers
    "shock_index",
    "hours_since_last_vitals",
    # Demographics and condition flags
    "patient_age",
    "has_copd",
    "has_post_op",
    "has_cardiac",
]


def extract_feature_vector(
    features: PatientFeatures,
    patient: Optional[Patient] = None,
) -> List[float]:
    """Convert PatientFeatures and optional Patient object into a flat float list.
    
    Missing values are represented as float('nan') which LightGBM handles natively.
    """
    row: List[float] = []

    def _v(val: Optional[float]) -> float:
        return float(val) if val is not None else float("nan")

    # Vitals in canonical order
    vitals_order = [
        VitalName.HR,
        VitalName.SBP,
        VitalName.DBP,
        VitalName.RR,
        VitalName.SPO2,
        VitalName.TEMP,
    ]

    for vital in vitals_order:
        b = features.baselines.get(vital)
        if b is not None:
            row.append(_v(b.current_value))
            row.append(_v(b.z_score))
            row.append(_v(b.trend_per_hour))
            row.append(_v(b.age_hours))
        else:
            row.extend([float("nan"), 0.0, float("nan"), float("nan")])

    # Aggregate physiological markers
    row.append(_v(features.shock_index))
    row.append(_v(features.hours_since_last_vitals))

    # Demographics
    if patient is not None and patient.age is not None:
        row.append(float(patient.age))
    else:
        row.append(float("nan"))

    # Conditions
    if patient is not None:
        row.append(1.0 if Condition.COPD in patient.conditions else 0.0)
        row.append(1.0 if Condition.POST_OP in patient.conditions else 0.0)
        row.append(1.0 if Condition.CARDIAC in patient.conditions else 0.0)
    else:
        row.extend([0.0, 0.0, 0.0])

    return row
