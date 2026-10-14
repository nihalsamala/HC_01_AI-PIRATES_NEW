"""
Transparent rule-based risk scoring and clinical risk tier allocation.

Combines NEWS2 physiological severity, personal baseline deviation, vital trends,
and shock index, with an optional machine learning blending hook.
"""

from typing import List, Optional, Tuple

from shared.schemas import (
    Condition,
    EngineConfig,
    Patient,
    RiskTier,
    VitalName,
    VitalsBase,
    VitalsReading,
)
from engine.features import PatientFeatures, extract_features
from engine.news2 import news2_components, news2_score
from engine.safety import check_red_lines, is_crash

# Machine Learning blending parameters (P8)
ENABLE_ML: bool = False  # Off by default per safety requirement
ML_WEIGHT: float = 0.30
RULE_WEIGHT: float = 0.70


def calculate_risk(
    features: PatientFeatures,
    reading: Optional[VitalsBase],
    patient: Patient,
    config: EngineConfig,
    ml_score: Optional[float] = None,
) -> Tuple[float, RiskTier, bool, List[str]]:
    """Calculate clinical risk score (0.0 to 1.0), risk tier, crash status, and plain reasons.
    
    Returns:
        (risk_score, risk_tier, is_crash_flag, reasons)
    """
    reasons: List[str] = []

    # 1. Immediate Crash Check (Unequivocal physiological collapse)
    crash_active = is_crash(reading)
    if crash_active and reading is not None:
        reasons.append("CRASH: Unequivocal physiological collapse")
        if reading.sbp is not None and reading.hr is not None:
            reasons.append(f"Severe shock: SBP {reading.sbp:.0f} mmHg, HR {reading.hr:.0f} bpm")
        if reading.spo2 is not None and reading.spo2 <= 88:
            reasons.append(f"Critical hypoxia: SpO2 {reading.spo2:.0f}%")
        return 0.98, RiskTier.CRITICAL, True, reasons

    # 2. Check for empty or all-None readings
    if reading is None or not reading.measured():
        return 0.0, RiskTier.LOW, False, ["No vitals recorded"]

    # 3. Check Hard Red Lines
    red_line_breached, red_line_reasons = check_red_lines(reading, patient, config)

    # 4. Standard NEWS2 calculation
    comp = news2_components(reading, patient, config)
    raw_news2 = comp["total"]

    # 5. Baseline Deviation & Trend Evaluation
    # If the patient has chronic conditions (e.g. COPD), determine if current vitals
    # simply match their chronic baseline
    b_rr = features.baselines.get(VitalName.RR)
    b_spo2 = features.baselines.get(VitalName.SPO2)
    b_sbp = features.baselines.get(VitalName.SBP)
    b_hr = features.baselines.get(VitalName.HR)

    # Base risk derived from NEWS2
    # Standard scale: 0-4 low, 5-6 medium, 7+ high
    score_from_news2 = min(0.45, raw_news2 * 0.06)

    # Adjust for chronic baseline stability (e.g., COPD patient at RR 22, SpO2 91)
    is_copd = Condition.COPD in patient.conditions
    if is_copd and b_rr and b_spo2:
        # Check if RR and SpO2 are close to their established personal baseline
        rr_stable = abs(b_rr.z_score) <= 1.2
        spo2_stable = abs(b_spo2.z_score) <= 1.2
        if rr_stable and spo2_stable and not red_line_breached:
            # Discount the false alarm points that fixed NEWS2 awards for chronic hypoxia/tachypnea
            score_from_news2 = min(0.20, score_from_news2 * 0.35)
            reasons.append(f"Stable COPD baseline (RR {b_rr.current_value:.0f}, SpO2 {b_spo2.current_value:.0f}%)")

    # Acute deviation penalties
    deviation_penalty = 0.0
    if b_rr and b_rr.z_score > 2.0:
        boost = min(0.25, (b_rr.z_score - 1.5) * 0.06)
        deviation_penalty += boost
        reasons.append(f"RR elevated vs baseline ({b_rr.effective_baseline:.0f} -> {b_rr.current_value:.0f})")

    if b_sbp and b_sbp.z_score < -1.5:
        boost = min(0.25, abs(b_sbp.z_score + 1.0) * 0.10)
        deviation_penalty += boost
        reasons.append(f"SBP falling vs baseline ({b_sbp.effective_baseline:.0f} -> {b_sbp.current_value:.0f} mmHg)")

    # Trend penalties (rates of change)
    trend_penalty = 0.0
    if b_rr and b_rr.trend_per_hour and b_rr.trend_per_hour >= 0.8:
        trend_penalty += 0.12
        reasons.append(f"RR rising rapidly (+{b_rr.trend_per_hour:.1f}/h)")

    if b_hr and b_hr.trend_per_hour and b_hr.trend_per_hour >= 4.0:
        trend_penalty += 0.10
        reasons.append(f"Pulse rising (+{b_hr.trend_per_hour:.1f} bpm/h)")

    # Shock index penalty
    si_penalty = 0.0
    if features.shock_index is not None:
        if features.shock_index >= 1.0:
            si_penalty += 0.18
            reasons.append(f"Elevated shock index {features.shock_index:.2f} (HR/SBP >= 1.0)")
        elif features.shock_index >= 0.85:
            si_penalty += 0.08
            reasons.append(f"Borderline shock index {features.shock_index:.2f}")

    # Combine transparent rule components
    total_rule_score = min(0.92, score_from_news2 + deviation_penalty + trend_penalty + si_penalty)

    # 6. Safety Rule: Hard Red Lines Override
    # A personal baseline can NEVER suppress an absolute red-line breach
    if red_line_breached:
        total_rule_score = max(total_rule_score, config.tier_high)
        for rlr in red_line_reasons:
            if rlr not in reasons:
                reasons.append(rlr)

    # 7. Optional Machine Learning Score Blending Hook
    if ml_score is None and ENABLE_ML:
        try:
            from ml.predict import ml_score as get_ml_score
            ml_score = get_ml_score(features, patient)
        except Exception:
            ml_score = None

    if ml_score is not None:
        final_score = round(RULE_WEIGHT * total_rule_score + ML_WEIGHT * ml_score, 3)
        if ml_score >= 0.70:
            reasons.append(f"ML early deterioration warning ({ml_score:.0%})")
    else:
        final_score = round(total_rule_score, 3)

    # Safety Floor Guarantee:
    # A personal baseline or ML score can NEVER suppress an absolute red-line breach
    if red_line_breached:
        final_score = max(final_score, config.tier_high)

    final_score = max(0.0, min(1.0, final_score))

    # 8. Map to Risk Tier using config cutoffs
    if final_score < config.tier_medium:
        tier = RiskTier.LOW
    elif final_score < config.tier_high:
        tier = RiskTier.MEDIUM
    elif final_score < config.tier_critical:
        tier = RiskTier.HIGH
    else:
        tier = RiskTier.CRITICAL

    if not reasons:
        reasons.append(f"Stable vitals (NEWS2 score {raw_news2})")

    return final_score, tier, False, reasons
