"""
Task generation module for WardPulse.

Converts PatientAssessment and FreshnessResult into candidate Tasks strictly using
the closed set in schemas.py and TASK_TITLES.
Enforces the fundamental clinical rule:
- Fresh + high risk -> page_doctor
- Stale + borderline risk -> repeat_* (or full_vitals_recheck), NEVER page_doctor
- Crash -> page_doctor with emergency=True
"""

from datetime import datetime
from typing import Dict, List, Optional

from shared.schemas import (
    Condition,
    Patient,
    PatientAssessment,
    RiskTier,
    Task,
    TaskStatus,
    TaskType,
    VitalName,
    TASK_TARGET_VITAL,
    TASK_TITLES,
)
from engine.features import PatientFeatures
from engine.freshness import FreshnessResult


def generate_candidate_tasks(
    patient: Patient,
    assessment: PatientAssessment,
    freshness: FreshnessResult,
    features: PatientFeatures,
    now: datetime,
) -> List[Task]:
    """Generate candidate Task cards for a patient based on clinical risk and data freshness."""
    tasks: List[Task] = []
    bed = patient.bed
    p_id = patient.id
    reading = features.latest_reading

    # 1. CRASH CASE -> page_doctor with emergency=True
    if assessment.crash:
        title = TASK_TITLES[TaskType.PAGE_DOCTOR].format(bed=bed)
        reason = " ; ".join(assessment.reasons) if assessment.reasons else "Unequivocal physiological crash"
        tasks.append(
            Task(
                id=0,  # Will be assigned deterministically in prioritizer
                patient_id=p_id,
                bed=bed,
                type=TaskType.PAGE_DOCTOR,
                target_vital=TASK_TARGET_VITAL.get(TaskType.PAGE_DOCTOR),
                title=title,
                reason=reason,
                priority=10.0 + assessment.risk_score,
                status=TaskStatus.ACTIVE,
                emergency=True,
                escalated=False,
                created_at=now,
                waiting_minutes=0.0,
            )
        )
        return tasks

    # 2. FRESH + HIGH / CRITICAL RISK -> page_doctor
    if assessment.risk_tier in (RiskTier.HIGH, RiskTier.CRITICAL):
        title = TASK_TITLES[TaskType.PAGE_DOCTOR].format(bed=bed)
        reason = " ; ".join(assessment.reasons) if assessment.reasons else "Acute deterioration detected"
        base_priority = 3.0 + (assessment.risk_score * 2.0)

        tasks.append(
            Task(
                id=0,
                patient_id=p_id,
                bed=bed,
                type=TaskType.PAGE_DOCTOR,
                target_vital=TASK_TARGET_VITAL.get(TaskType.PAGE_DOCTOR),
                title=title,
                reason=reason,
                priority=base_priority,
                status=TaskStatus.ACTIVE,
                emergency=False,
                escalated=False,
                created_at=now,
                waiting_minutes=0.0,
            )
        )

        # Secondary supportive cards if vitals suggest specific bedside actions
        if reading is not None:
            # Check oxygen cannula if on oxygen with low saturation
            if reading.on_oxygen and reading.spo2 is not None and reading.spo2 < 95.0:
                cannula_title = TASK_TITLES[TaskType.CHECK_OXYGEN_CANNULA].format(bed=bed)
                tasks.append(
                    Task(
                        id=0,
                        patient_id=p_id,
                        bed=bed,
                        type=TaskType.CHECK_OXYGEN_CANNULA,
                        target_vital=TASK_TARGET_VITAL.get(TaskType.CHECK_OXYGEN_CANNULA),
                        title=cannula_title,
                        reason=f"SpO2 {reading.spo2:.0f}% despite supplemental oxygen",
                        priority=base_priority - 0.2,
                        status=TaskStatus.QUEUED,
                        emergency=False,
                        escalated=False,
                        created_at=now,
                        waiting_minutes=0.0,
                    )
                )

            # Sit patient upright if severe tachypnea
            if reading.rr is not None and reading.rr >= 24.0:
                sit_title = TASK_TITLES[TaskType.SIT_UPRIGHT].format(bed=bed)
                tasks.append(
                    Task(
                        id=0,
                        patient_id=p_id,
                        bed=bed,
                        type=TaskType.SIT_UPRIGHT,
                        target_vital=TASK_TARGET_VITAL.get(TaskType.SIT_UPRIGHT),
                        title=sit_title,
                        reason=f"Tachypnea RR {reading.rr:.0f} breaths/min; improve lung mechanics",
                        priority=base_priority - 0.3,
                        status=TaskStatus.QUEUED,
                        emergency=False,
                        escalated=False,
                        created_at=now,
                        waiting_minutes=0.0,
                    )
                )

        return tasks

    # 3. BORDERLINE RISK + STALE DATA (Story 2) -> repeat_* or full_vitals_recheck
    # Rule: NEVER page_doctor from stale data alone
    if freshness.is_borderline_and_stale or (len(freshness.stale_vitals) > 0 and assessment.risk_tier == RiskTier.MEDIUM):
        stale_list = freshness.stale_vitals

        # If 3 or more vitals are stale, or overall reading is very old -> full_vitals_recheck
        if len(stale_list) >= 3 or (freshness.hours_since_last_vitals and freshness.hours_since_last_vitals >= 6.0):
            title = TASK_TITLES[TaskType.FULL_VITALS_RECHECK].format(bed=bed)
            last_h = f"{freshness.hours_since_last_vitals:.0f}h" if freshness.hours_since_last_vitals else "unknown"
            reason = f"Full vitals overdue; last taken {last_h} ago"
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.FULL_VITALS_RECHECK,
                    target_vital=None,
                    title=title,
                    reason=reason,
                    priority=1.5 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )
            return tasks

        # Otherwise, generate specific repeat_* card for the stale vital
        if VitalName.SBP in stale_list or VitalName.DBP in stale_list:
            b_sbp = features.baselines.get(VitalName.SBP)
            sbp_age = f"{b_sbp.age_hours:.0f}h" if b_sbp and b_sbp.age_hours else "overdue"
            prev_sbp = f"{b_sbp.current_value:.0f}" if b_sbp and b_sbp.current_value else "borderline"
            title = TASK_TITLES[TaskType.REPEAT_BP].format(bed=bed)
            reason = f"BP not taken for {sbp_age}; prior SBP {prev_sbp} mmHg"
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.REPEAT_BP,
                    target_vital=VitalName.SBP,
                    title=title,
                    reason=reason,
                    priority=1.8 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )

        if VitalName.RR in stale_list:
            b_rr = features.baselines.get(VitalName.RR)
            rr_age = f"{b_rr.age_hours:.0f}h" if b_rr and b_rr.age_hours else "overdue"
            title = TASK_TITLES[TaskType.REPEAT_RESP_RATE].format(bed=bed)
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.REPEAT_RESP_RATE,
                    target_vital=VitalName.RR,
                    title=title,
                    reason=f"Respiratory rate not taken for {rr_age}",
                    priority=1.7 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )

        if VitalName.SPO2 in stale_list:
            b_spo2 = features.baselines.get(VitalName.SPO2)
            spo2_age = f"{b_spo2.age_hours:.0f}h" if b_spo2 and b_spo2.age_hours else "overdue"
            title = TASK_TITLES[TaskType.REPEAT_SPO2].format(bed=bed)
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.REPEAT_SPO2,
                    target_vital=VitalName.SPO2,
                    title=title,
                    reason=f"SpO2 not checked for {spo2_age}",
                    priority=1.6 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )

        if VitalName.HR in stale_list:
            b_hr = features.baselines.get(VitalName.HR)
            hr_age = f"{b_hr.age_hours:.0f}h" if b_hr and b_hr.age_hours else "overdue"
            title = TASK_TITLES[TaskType.REPEAT_HEART_RATE].format(bed=bed)
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.REPEAT_HEART_RATE,
                    target_vital=VitalName.HR,
                    title=title,
                    reason=f"Pulse not checked for {hr_age}",
                    priority=1.5 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )

        if VitalName.TEMP in stale_list:
            b_temp = features.baselines.get(VitalName.TEMP)
            temp_age = f"{b_temp.age_hours:.0f}h" if b_temp and b_temp.age_hours else "overdue"
            title = TASK_TITLES[TaskType.REPEAT_TEMP].format(bed=bed)
            tasks.append(
                Task(
                    id=0,
                    patient_id=p_id,
                    bed=bed,
                    type=TaskType.REPEAT_TEMP,
                    target_vital=VitalName.TEMP,
                    title=title,
                    reason=f"Temperature not checked for {temp_age}",
                    priority=1.3 + assessment.risk_score,
                    status=TaskStatus.ACTIVE,
                    emergency=False,
                    escalated=False,
                    created_at=now,
                    waiting_minutes=0.0,
                )
            )

    return tasks
