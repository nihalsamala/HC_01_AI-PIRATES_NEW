"""
Contract tests for WardPulse Engine B (freshness, tasks, prioritizer, pipeline).

Tests contract specifications 1 to 8 and 10 from docs/contracts.md section 10.
Uses hand-built fixtures from tests/fixtures.py (NO simulator import).
"""

from datetime import datetime, timedelta
import pytest

from shared.schemas import (
    Condition,
    EngineConfig,
    Mode,
    Patient,
    Source,
    TaskStatus,
    TaskType,
    VitalName,
    VitalsReading,
)
from engine.pipeline import evaluate_ward
from engine.news2 import evaluate_ward_news2
from tests.fixtures import (
    FIXTURE_BASE_TIME,
    build_10_abnormal_patients_fixtures,
    build_story1_fixtures,
    build_story2_fixtures,
    build_story3_fixtures,
)


@pytest.fixture
def default_config():
    return EngineConfig()


def test_contract_1_story_1_bed3_no_card_bed7_active(default_config):
    """Contract Test 1: Bed 3 at RR 22 yields no card; Bed 7 at RR 22 yields an active card."""
    now = FIXTURE_BASE_TIME + timedelta(hours=1)
    patients, vitals = build_story1_fixtures(now)

    evaluation = evaluate_ward(patients, vitals, now, default_config)

    active_patient_ids = [t.patient_id for t in evaluation.tasks.active]
    all_task_patient_ids = [
        t.patient_id for t in (evaluation.tasks.emergency + evaluation.tasks.active + evaluation.tasks.queue)
    ]

    # Bed 7 is deteriorating post-op -> must have an active card
    assert 7 in active_patient_ids
    assert any(t.patient_id == 7 and t.type == TaskType.PAGE_DOCTOR for t in evaluation.tasks.active)

    # Bed 3 is stable COPD baseline -> must have NO card
    assert 3 not in all_task_patient_ids


def test_contract_2_story_2_stale_bp_gives_repeat_bp(default_config):
    """Contract Test 2: Bed 4 with stale BP yields repeat_bp, NOT page_doctor."""
    now = FIXTURE_BASE_TIME + timedelta(hours=3)
    patients, vitals = build_story2_fixtures(now)

    evaluation = evaluate_ward(patients, vitals, now, default_config)

    bed4_tasks = [
        t for t in (evaluation.tasks.active + evaluation.tasks.queue)
        if t.patient_id == 4
    ]

    assert len(bed4_tasks) > 0
    # Must yield repeat_bp
    assert any(t.type == TaskType.REPEAT_BP for t in bed4_tasks)
    # Must NEVER page doctor from stale data alone
    assert not any(t.type == TaskType.PAGE_DOCTOR for t in bed4_tasks)


def test_contract_3_story_3_crash_in_emergency_active_still_holds_2(default_config):
    """Contract Test 3: With 2 active cards, crash on Bed 12 appears in emergency and active still has 2."""
    now = FIXTURE_BASE_TIME + timedelta(hours=5)
    patients, vitals = build_story3_fixtures(now)

    evaluation = evaluate_ward(patients, vitals, now, default_config)

    # Attention budget on active cards
    assert len(evaluation.tasks.active) == default_config.k_budget
    assert len(evaluation.tasks.active) == 2

    # Bed 12 must appear in emergency banner outside the budget
    assert len(evaluation.tasks.emergency) >= 1
    emergency_patient_ids = [t.patient_id for t in evaluation.tasks.emergency]
    assert 12 in emergency_patient_ids

    bed12_emergency = next(t for t in evaluation.tasks.emergency if t.patient_id == 12)
    assert bed12_emergency.emergency is True
    assert bed12_emergency.type == TaskType.PAGE_DOCTOR


def test_contract_4_budget_10_abnormal_patients(default_config):
    """Contract Test 4: With 10 abnormal patients, len(active) <= k_budget in WardPulse mode."""
    now = FIXTURE_BASE_TIME + timedelta(hours=2)
    patients, vitals = build_10_abnormal_patients_fixtures(now)

    evaluation = evaluate_ward(patients, vitals, now, default_config)

    # Strict attention budget K=2
    assert len(evaluation.tasks.active) <= default_config.k_budget
    assert len(evaluation.tasks.active) == default_config.k_budget

    # The remaining abnormal patients are prioritized in queue
    assert len(evaluation.tasks.queue) > 0
    assert len(evaluation.tasks.queue) == len(patients) - default_config.k_budget


def test_contract_5_naive_mode_shows_more_alerts_than_wardpulse(default_config):
    """Contract Test 5: Naive mode on the same data shows more alerts_shown than WardPulse mode."""
    now = FIXTURE_BASE_TIME + timedelta(hours=2)
    patients, vitals = build_10_abnormal_patients_fixtures(now)

    eval_wardpulse = evaluate_ward(patients, vitals, now, default_config)
    eval_naive = evaluate_ward_news2(patients, vitals, now, default_config)

    # WardPulse limits active alerts to K=2 (plus emergency)
    assert eval_wardpulse.tasks.alerts_shown <= default_config.k_budget + len(eval_wardpulse.tasks.emergency)

    # Naive mode has no budget and alerts on all 10 abnormal patients
    assert eval_naive.tasks.alerts_shown > eval_wardpulse.tasks.alerts_shown
    assert eval_naive.tasks.alerts_shown == 10


def test_contract_6_aging_increases_priority(default_config):
    """Contract Test 6: A queued task's priority increases with waiting time."""
    now = FIXTURE_BASE_TIME + timedelta(hours=2)
    patients, vitals = build_10_abnormal_patients_fixtures(now)

    # 1. Initial evaluation
    eval1 = evaluate_ward(patients, vitals, now, default_config)
    assert len(eval1.tasks.queue) > 0
    queued_task_1 = eval1.tasks.queue[0]
    initial_priority = queued_task_1.priority

    # 2. Advance time by 2 hours without completing the queued task
    later = now + timedelta(hours=2)
    eval2 = evaluate_ward(
        patients,
        vitals,
        later,
        default_config,
        previous_tasks=eval1.tasks.active + eval1.tasks.queue,
    )

    # Find the same task by (patient_id, type)
    matching_tasks = [
        t for t in (eval2.tasks.active + eval2.tasks.queue)
        if t.patient_id == queued_task_1.patient_id and t.type == queued_task_1.type
    ]
    assert len(matching_tasks) == 1
    aged_task = matching_tasks[0]

    # Priority must have increased due to aging
    assert aged_task.priority > initial_priority
    expected_boost = default_config.aging_per_hour * 2.0
    assert aged_task.priority >= initial_priority + (expected_boost - 0.05)


def test_contract_7_escalation_after_threshold(default_config):
    """Contract Test 7: An ignored active task becomes escalated after escalation_after_minutes."""
    now = FIXTURE_BASE_TIME + timedelta(hours=1)
    patients, vitals = build_story1_fixtures(now)

    eval1 = evaluate_ward(patients, vitals, now, default_config)
    bed7_task = next(t for t in eval1.tasks.active if t.patient_id == 7)
    assert bed7_task.escalated is False

    # Advance past escalation_after_minutes (default 30 mins) -> 45 mins later
    later = now + timedelta(minutes=45)
    eval2 = evaluate_ward(
        patients,
        vitals,
        later,
        default_config,
        previous_tasks=eval1.tasks.active,
    )

    bed7_task_later = next(t for t in eval2.tasks.active if t.patient_id == 7)
    assert bed7_task_later.escalated is True
    assert bed7_task_later.waiting_minutes >= 30.0


def test_contract_8_all_none_vitals_do_not_crash(default_config):
    """Contract Test 8: A patient with all vitals None does not crash the engine."""
    now = FIXTURE_BASE_TIME
    empty_patient = Patient(
        id=99,
        bed=99,
        age=45,
        conditions=[],
        admitted_at=now,
        display_name="Bed 99",
    )
    empty_vitals = {99: []}

    evaluation = evaluate_ward([empty_patient], empty_vitals, now, default_config)
    assert len(evaluation.assessments) == 1
    assert evaluation.assessments[0].risk_score == 0.0
    assert len(evaluation.tasks.active) == 0


def test_contract_10_safety_never_suppresses_red_line(default_config):
    """Contract Test 10: Personal baseline never suppresses an absolute red-line breach."""
    now = FIXTURE_BASE_TIME
    patient = Patient(
        id=50,
        bed=5,
        age=60,
        conditions=[],
        admitted_at=now - timedelta(days=2),
    )
    # Severe drop into SBP <= 90 (red line)
    vitals = {
        50: [
            VitalsReading(id=1, patient_id=50, timestamp=now - timedelta(hours=4), source=Source.MANUAL, hr=75.0, sbp=110.0, dbp=70.0, rr=16.0, spo2=98.0),
            VitalsReading(id=2, patient_id=50, timestamp=now, source=Source.MANUAL, hr=78.0, sbp=86.0, dbp=54.0, rr=16.0, spo2=98.0),
        ]
    }

    eval_result = evaluate_ward([patient], vitals, now, default_config)
    assert len(eval_result.assessments) == 1
    assert eval_result.assessments[0].risk_score >= default_config.tier_high
    assert any(t.patient_id == 50 and t.type == TaskType.PAGE_DOCTOR for t in eval_result.tasks.active)
