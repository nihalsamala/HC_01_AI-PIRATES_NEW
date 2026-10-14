"""
Standard NEWS2 (National Early Warning Score 2) calculation and evaluation.

Based on the Royal College of Physicians (RCP) NEWS2 clinical chart (2017).
Acts as the honest comparator ("Naive AI") in WardPulse.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.schemas import (
    Condition,
    Consciousness,
    EngineConfig,
    Mode,
    Patient,
    PatientAssessment,
    RiskTier,
    Task,
    TasksResponse,
    TaskStatus,
    TaskType,
    VitalsBase,
    VitalsIn,
    VitalsReading,
    WardBed,
    WardEvaluation,
    WardOverview,
    WardStatus,
    TASK_TITLES,
)


def news2_components(
    reading: Optional[VitalsBase],
    patient: Patient,
    config: EngineConfig,
) -> Dict[str, Any]:
    """Calculate individual NEWS2 component scores according to RCP guidelines.
    
    Treats missing vitals as 0 points and records them in the 'missing' list.
    """
    scores: Dict[str, int] = {
        "rr": 0,
        "spo2": 0,
        "on_oxygen": 0,
        "sbp": 0,
        "hr": 0,
        "consciousness": 0,
        "temp": 0,
    }
    missing: List[str] = []

    if reading is None:
        return {
            "scores": scores,
            "total": 0,
            "missing": ["rr", "spo2", "on_oxygen", "sbp", "hr", "consciousness", "temp"],
            "scale2_used": False,
        }

    # 1. Respiration Rate (breaths/min)
    if reading.rr is not None:
        rr = reading.rr
        if rr <= 8:
            scores["rr"] = 3
        elif 9 <= rr <= 11:
            scores["rr"] = 1
        elif 12 <= rr <= 20:
            scores["rr"] = 0
        elif 21 <= rr <= 24:
            scores["rr"] = 2
        else:  # rr >= 25
            scores["rr"] = 3
    else:
        missing.append("rr")

    # 2. Oxygen Saturation (SpO2 %)
    use_scale2 = config.news2_spo2_scale2_for_copd and (Condition.COPD in patient.conditions)
    if reading.spo2 is not None:
        spo2 = reading.spo2
        if not use_scale2:
            # Scale 1 (standard)
            if spo2 <= 91:
                scores["spo2"] = 3
            elif 92 <= spo2 <= 93:
                scores["spo2"] = 2
            elif 94 <= spo2 <= 95:
                scores["spo2"] = 1
            else:  # >= 96
                scores["spo2"] = 0
        else:
            # Scale 2 (hypercapnic respiratory failure / COPD target 88-92%)
            if spo2 <= 83:
                scores["spo2"] = 3
            elif 84 <= spo2 <= 85:
                scores["spo2"] = 2
            elif 86 <= spo2 <= 87:
                scores["spo2"] = 1
            elif 88 <= spo2 <= 92:
                scores["spo2"] = 0
            else:  # >= 93
                if reading.on_oxygen:
                    if 93 <= spo2 <= 94:
                        scores["spo2"] = 1
                    elif 95 <= spo2 <= 96:
                        scores["spo2"] = 2
                    else:  # >= 97
                        scores["spo2"] = 3
                else:
                    scores["spo2"] = 0
    else:
        missing.append("spo2")

    # 3. Supplemental Oxygen
    if reading.on_oxygen:
        scores["on_oxygen"] = 2
    else:
        scores["on_oxygen"] = 0

    # 4. Systolic Blood Pressure (mmHg)
    if reading.sbp is not None:
        sbp = reading.sbp
        if sbp <= 90:
            scores["sbp"] = 3
        elif 91 <= sbp <= 100:
            scores["sbp"] = 2
        elif 101 <= sbp <= 110:
            scores["sbp"] = 1
        elif 111 <= sbp <= 219:
            scores["sbp"] = 0
        else:  # sbp >= 220
            scores["sbp"] = 3
    else:
        missing.append("sbp")

    # 5. Pulse / Heart Rate (bpm)
    if reading.hr is not None:
        hr = reading.hr
        if hr <= 40:
            scores["hr"] = 3
        elif 41 <= hr <= 50:
            scores["hr"] = 1
        elif 51 <= hr <= 90:
            scores["hr"] = 0
        elif 91 <= hr <= 110:
            scores["hr"] = 1
        elif 111 <= hr <= 130:
            scores["hr"] = 2
        else:  # hr >= 131
            scores["hr"] = 3
    else:
        missing.append("hr")

    # 6. Consciousness (ACVPU)
    if reading.consciousness is not None:
        if reading.consciousness == Consciousness.ALERT:
            scores["consciousness"] = 0
        else:
            scores["consciousness"] = 3
    else:
        missing.append("consciousness")

    # 7. Temperature (Celsius)
    if reading.temp is not None:
        temp = reading.temp
        if temp <= 35.0:
            scores["temp"] = 3
        elif 35.1 <= temp <= 36.0:
            scores["temp"] = 1
        elif 36.1 <= temp <= 38.0:
            scores["temp"] = 0
        elif 38.1 <= temp <= 39.0:
            scores["temp"] = 1
        else:  # temp >= 39.1
            scores["temp"] = 2
    else:
        missing.append("temp")

    total = sum(scores.values())
    return {
        "scores": scores,
        "total": total,
        "missing": missing,
        "scale2_used": use_scale2,
    }


def news2_score(
    reading: Optional[VitalsBase],
    patient: Patient,
    config: EngineConfig,
) -> int:
    """Calculate aggregate NEWS2 integer score."""
    comp = news2_components(reading, patient, config)
    return comp["total"]


def evaluate_ward_news2(
    patients: List[Patient],
    vitals: Dict[int, List[VitalsReading]],
    now: datetime,
    config: EngineConfig,
    previous_tasks: Optional[List[Task]] = None,
) -> WardEvaluation:
    """Evaluate all ward patients under naive NEWS2 alerting rules.
    
    Alert rule: score >= config.news2_alert_threshold OR any single parameter scores 3.
    Every flagged patient becomes a Task of type news2_alert in `active`.
    No budget constraint (budget_k=None).
    """
    assessments: List[PatientAssessment] = []
    active_tasks: List[Task] = []
    ward_beds: List[WardBed] = []

    task_counter = 1

    for p in patients:
        p_readings = vitals.get(p.id, [])
        latest_reading = p_readings[-1] if p_readings else None

        comp = news2_components(latest_reading, p, config)
        score = comp["total"]
        any_score_3 = any(s == 3 for s in comp["scores"].values())

        # Determine risk tier from NEWS2 guidance
        if score == 0:
            tier = RiskTier.LOW
            bed_status = WardStatus.STABLE
        elif score <= 4 and not any_score_3:
            tier = RiskTier.LOW
            bed_status = WardStatus.WATCH
        elif (5 <= score <= 6) or any_score_3:
            tier = RiskTier.MEDIUM
            bed_status = WardStatus.ACTION
        else:  # score >= 7
            tier = RiskTier.HIGH
            bed_status = WardStatus.CRITICAL

        reasons = [f"NEWS2 aggregate score: {score}"]
        if any_score_3:
            red_params = [k for k, v in comp["scores"].items() if v == 3]
            reasons.append(f"Score 3 parameter(s): {', '.join(red_params)}")

        # Check naive alert rule
        alert_raised = (score >= config.news2_alert_threshold) or any_score_3

        if alert_raised:
            title_template = TASK_TITLES.get(TaskType.NEWS2_ALERT, "Abnormal vitals: Bed {bed}")
            title = title_template.format(bed=p.bed)
            task_reason = f"NEWS2 score {score}"
            if any_score_3:
                task_reason += " (contains red-line parameter score 3)"

            active_tasks.append(
                Task(
                    id=task_counter,
                    patient_id=p.id,
                    bed=p.bed,
                    type=TaskType.NEWS2_ALERT,
                    title=title,
                    reason=task_reason,
                    priority=float(score),
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )
            task_counter += 1

        assessment = PatientAssessment(
            patient_id=p.id,
            bed=p.bed,
            risk_score=min(1.0, score / 15.0),
            risk_tier=tier,
            crash=False,
            stale_vitals=[],
            hours_since_last_vitals=(
                (now - latest_reading.timestamp).total_seconds() / 3600.0
                if latest_reading else None
            ),
            next_vitals_due=None,
            news2_score=score if latest_reading else None,
            reasons=reasons,
        )
        assessments.append(assessment)

        ward_beds.append(
            WardBed(
                patient_id=p.id,
                bed=p.bed,
                conditions=p.conditions,
                status=bed_status,
                risk_tier=tier,
                data_stale=False,
                hours_since_last_vitals=assessment.hours_since_last_vitals,
                has_open_task=alert_raised,
            )
        )

    # Sort active tasks by score descending
    active_tasks.sort(key=lambda t: t.priority, reverse=True)

    tasks_response = TasksResponse(
        mode=Mode.NEWS2,
        now=now,
        budget_k=None,
        emergency=[],
        active=active_tasks,
        queue=[],
    )

    ward_overview = WardOverview(now=now, beds=ward_beds)

    return WardEvaluation(
        assessments=assessments,
        tasks=tasks_response,
        ward=ward_overview,
    )
