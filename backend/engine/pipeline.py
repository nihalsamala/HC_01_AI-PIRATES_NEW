"""
WardPulse attention allocation pipeline.

Wires together features -> safety + risk -> freshness -> tasks -> prioritizer,
filling assessments, prioritized tasks, and the whole-ward overview.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set

from shared.schemas import (
    EngineConfig,
    Mode,
    Patient,
    PatientAssessment,
    RiskTier,
    Task,
    TasksResponse,
    VitalsReading,
    WardBed,
    WardEvaluation,
    WardOverview,
    WardStatus,
)
from engine.features import extract_features
from engine.freshness import calculate_freshness
from engine.news2 import news2_score
from engine.prioritizer import prioritize_tasks
from engine.risk import calculate_risk
from engine.tasks import generate_candidate_tasks


def evaluate_ward(
    patients: List[Patient],
    vitals: Dict[int, List[VitalsReading]],
    now: datetime,
    config: EngineConfig,
    previous_tasks: Optional[List[Task]] = None,
) -> WardEvaluation:
    """Evaluate all ward patients and allocate nurse attention (WardPulse mode)."""
    assessments: List[PatientAssessment] = []
    all_candidates: List[Task] = []
    bed_data_stale: Dict[int, bool] = {}
    bed_statuses: Dict[int, WardStatus] = {}

    for p in patients:
        p_readings = vitals.get(p.id, [])
        features = extract_features(p, p_readings, now, config)
        latest_reading = features.latest_reading

        risk_score, risk_tier, is_crash_flag, reasons = calculate_risk(
            features, latest_reading, p, config
        )

        freshness = calculate_freshness(
            p.id, risk_tier, risk_score, features, now, config
        )

        n2_score = news2_score(latest_reading, p, config) if latest_reading else None

        assessment = PatientAssessment(
            patient_id=p.id,
            bed=p.bed,
            risk_score=risk_score,
            risk_tier=risk_tier,
            crash=is_crash_flag,
            stale_vitals=freshness.stale_vitals,
            hours_since_last_vitals=freshness.hours_since_last_vitals,
            next_vitals_due=freshness.next_vitals_due,
            news2_score=n2_score,
            reasons=reasons,
        )
        assessments.append(assessment)

        # Generate candidate tasks
        cand_tasks = generate_candidate_tasks(p, assessment, freshness, features, now)
        all_candidates.extend(cand_tasks)

        # Determine bed status color on the ward strip
        if is_crash_flag:
            b_status = WardStatus.CRITICAL
        elif risk_tier in (RiskTier.HIGH, RiskTier.CRITICAL):
            b_status = WardStatus.ACTION
        elif freshness.is_borderline_and_stale or risk_tier == RiskTier.MEDIUM:
            b_status = WardStatus.WATCH
        else:
            b_status = WardStatus.STABLE

        bed_statuses[p.id] = b_status
        bed_data_stale[p.id] = freshness.is_data_stale

    # Run prioritizer: budget K, aging, escalation, and crash bypass
    tasks_response = prioritize_tasks(
        candidate_tasks=all_candidates,
        previous_tasks=previous_tasks,
        now=now,
        config=config,
    )

    # Beds with active or emergency cards
    active_patient_ids: Set[int] = {
        t.patient_id for t in (tasks_response.emergency + tasks_response.active)
    }

    # Build WardOverview
    ward_beds: List[WardBed] = []
    for p in patients:
        ass = next(a for a in assessments if a.patient_id == p.id)
        ward_beds.append(
            WardBed(
                patient_id=p.id,
                bed=p.bed,
                conditions=p.conditions,
                status=bed_statuses.get(p.id, WardStatus.STABLE),
                risk_tier=ass.risk_tier,
                data_stale=bed_data_stale.get(p.id, False),
                hours_since_last_vitals=ass.hours_since_last_vitals,
                has_open_task=p.id in active_patient_ids,
            )
        )

    return WardEvaluation(
        assessments=assessments,
        tasks=tasks_response,
        ward=WardOverview(now=now, beds=ward_beds),
    )
