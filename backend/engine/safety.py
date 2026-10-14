"""
Hard safety boundaries, red lines, and crash bypass evaluation for WardPulse.

Clinical rule: A personal baseline may reduce a false alarm ONLY inside safe limits,
and must NEVER suppress or override an absolute red-line breach.
"""

from typing import List, Optional, Tuple

from shared.schemas import (
    Condition,
    Consciousness,
    EngineConfig,
    Patient,
    VitalsBase,
)
from engine.news2 import news2_components, news2_score


def is_crash(reading: Optional[VitalsBase]) -> bool:
    """Evaluate whether a vitals set represents unequivocal clinical crash.
    
    Crash criteria represent immediate life-threatening physiological collapse:
    - Severe hypotension with severe tachycardia (SBP <= 80 and HR >= 130) [Story 3 criteria]
    - Severe hypotension with severe hypoxia (SBP <= 80 and SpO2 <= 88%)
    - Profound hypotension alone (SBP <= 70 mmHg)
    - Critical hypoxia alone (SpO2 <= 82%)
    - Extreme tachycardia (HR >= 140 bpm) with altered consciousness
    """
    if reading is None:
        return False

    sbp = reading.sbp
    hr = reading.hr
    spo2 = reading.spo2
    consciousness = reading.consciousness

    # Story 3 criteria: SBP ~78, HR ~135, SpO2 ~86
    if sbp is not None and hr is not None:
        if sbp <= 80.0 and hr >= 130.0:
            return True

    if sbp is not None and spo2 is not None:
        if sbp <= 80.0 and spo2 <= 88.0:
            return True

    if sbp is not None and sbp <= 70.0:
        return True

    if spo2 is not None and spo2 <= 82.0:
        return True

    if hr is not None and hr >= 140.0:
        if consciousness is not None and consciousness != Consciousness.ALERT:
            return True

    return False


def check_red_lines(
    reading: Optional[VitalsBase],
    patient: Patient,
    config: EngineConfig,
) -> Tuple[bool, List[str]]:
    """Evaluate absolute hard clinical red lines based on RCP NEWS2 maximum-score thresholds.
    
    Hard red lines trigger whenever ANY single physiological parameter breaches maximum score (3)
    or aggregate score reaches high risk (>= 7).
    These boundaries can NEVER be bypassed or softened by personal baseline calculations.
    """
    if reading is None:
        return False, []

    reasons: List[str] = []

    # Check crash first
    if is_crash(reading):
        reasons.append("CRASH: Unequivocal physiological collapse")
        if reading.sbp is not None and reading.hr is not None:
            reasons.append(f"Profound shock: SBP {reading.sbp} mmHg, HR {reading.hr} bpm")
        return True, reasons

    # Parameter-level hard limits
    comp = news2_components(reading, patient, config)
    scores = comp["scores"]
    is_copd = Condition.COPD in patient.conditions

    if scores.get("rr") == 3 and reading.rr is not None:
        reasons.append(f"Critical respiratory rate: {reading.rr} breaths/min")

    if reading.spo2 is not None:
        if is_copd:
            # In COPD, standard target is 88-92%. Red line is severe hypoxemia <= 88%
            if reading.spo2 <= 88.0:
                reasons.append(f"Critical hypoxia for COPD: SpO2 {reading.spo2}% (threshold <= 88%)")
        else:
            if scores.get("spo2") == 3:
                reasons.append(f"Critical hypoxia: SpO2 {reading.spo2}%")

    if scores.get("sbp") == 3 and reading.sbp is not None:
        reasons.append(f"Critical systolic blood pressure: {reading.sbp} mmHg")
    if scores.get("hr") == 3 and reading.hr is not None:
        reasons.append(f"Critical heart rate: {reading.hr} bpm")
    if scores.get("consciousness") == 3 and reading.consciousness is not None:
        reasons.append(f"Altered level of consciousness: {reading.consciousness.value}")
    if scores.get("temp") == 3 and reading.temp is not None:
        reasons.append(f"Critical temperature: {reading.temp} °C")

    # Aggregate level
    total_score = comp["total"]
    if total_score >= 7:
        reasons.append(f"High clinical risk aggregate NEWS2: {total_score} (threshold >= 7)")

    is_breached = len(reasons) > 0
    return is_breached, reasons
