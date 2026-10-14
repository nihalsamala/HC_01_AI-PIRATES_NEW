"""
Smoke tests for WardPulse data schemas and stubs.
"""

from datetime import datetime
import pytest
from pydantic import ValidationError

from shared.schemas import (
    Condition,
    EngineConfig,
    Mode,
    Patient,
    Task,
    TasksResponse,
    TaskStatus,
    TaskType,
    VitalsIn,
    WardEvaluation,
)
from engine.pipeline import evaluate_ward
from engine.news2 import evaluate_ward_news2
from simulator.ward import Simulator, build_ward


def test_valid_models_build():
    """(a) Test that valid Patient, VitalsIn, Task, TasksResponse build properly."""
    now = datetime(2026, 10, 20, 10, 0)
    
    patient = Patient(
        id=1,
        bed=1,
        age=65,
        conditions=[Condition.COPD],
        admitted_at=datetime(2026, 10, 20, 6, 0),
        display_name="Bed 1",
    )
    assert patient.id == 1
    assert patient.bed == 1
    assert patient.conditions == [Condition.COPD]

    vitals = VitalsIn(
        patient_id=1,
        timestamp=now,
        hr=78.0,
        sbp=122.0,
        dbp=76.0,
        rr=16.0,
        spo2=98.0,
        temp=36.7,
    )
    assert vitals.patient_id == 1
    assert vitals.hr == 78.0
    assert len(vitals.measured()) == 6

    task = Task(
        id=1,
        patient_id=1,
        bed=1,
        type=TaskType.PAGE_DOCTOR,
        title="Page the on-duty doctor: Bed 1",
        reason="RR 14 -> 22 over 5h; pulse rising",
        priority=2.5,
        status=TaskStatus.ACTIVE,
        created_at=now,
        waiting_minutes=0.0,
    )
    assert task.type == TaskType.PAGE_DOCTOR
    assert task.priority == 2.5

    tasks_resp = TasksResponse(
        mode=Mode.WARDPULSE,
        now=now,
        budget_k=2,
        emergency=[],
        active=[task],
        queue=[],
    )
    assert tasks_resp.mode == Mode.WARDPULSE
    assert tasks_resp.budget_k == 2
    assert len(tasks_resp.active) == 1


def test_sbp_less_than_dbp_raises():
    """(b) Test that sbp < dbp raises validation error."""
    with pytest.raises(ValidationError):
        VitalsIn(
            patient_id=1,
            sbp=70.0,
            dbp=90.0,
        )


def test_vitals_in_with_no_measurement_raises():
    """(c) Test that VitalsIn with no measurement raises validation error."""
    with pytest.raises(ValidationError):
        VitalsIn(patient_id=1)


def test_tasks_response_alerts_shown():
    """(d) Test that TasksResponse.alerts_shown equals len(emergency) + len(active)."""
    now = datetime(2026, 10, 20, 10, 0)
    task1 = Task(
        id=1,
        patient_id=1,
        bed=1,
        type=TaskType.PAGE_DOCTOR,
        title="Page the on-duty doctor: Bed 1",
        reason="Acute deterioration",
        priority=3.0,
        status=TaskStatus.ACTIVE,
        emergency=True,
        created_at=now,
    )
    task2 = Task(
        id=2,
        patient_id=2,
        bed=2,
        type=TaskType.REPEAT_BP,
        title="Repeat manual BP: Bed 2",
        reason="BP 7h old",
        priority=1.5,
        status=TaskStatus.ACTIVE,
        created_at=now,
    )
    task3 = Task(
        id=3,
        patient_id=3,
        bed=3,
        type=TaskType.REPEAT_SPO2,
        title="Recheck oxygen level: Bed 3",
        reason="Low SpO2",
        priority=1.2,
        status=TaskStatus.QUEUED,
        created_at=now,
    )

    resp = TasksResponse(
        mode=Mode.WARDPULSE,
        now=now,
        budget_k=2,
        emergency=[task1],
        active=[task2],
        queue=[task3],
    )
    assert resp.alerts_shown == len(resp.emergency) + len(resp.active)
    assert resp.alerts_shown == 2


def test_stubs_return_valid_ward_evaluations():
    """(e) Test that pipeline, news2, and simulator stubs return valid objects."""
    now = datetime(2026, 10, 20, 10, 0)
    config = EngineConfig()

    eval_wp = evaluate_ward(
        patients=[],
        vitals={},
        now=now,
        config=config,
    )
    assert isinstance(eval_wp, WardEvaluation)
    assert eval_wp.tasks.mode == Mode.WARDPULSE
    assert eval_wp.tasks.budget_k == config.k_budget
    assert eval_wp.assessments == []
    assert eval_wp.tasks.active == []

    eval_news2 = evaluate_ward_news2(
        patients=[],
        vitals={},
        now=now,
        config=config,
    )
    assert isinstance(eval_news2, WardEvaluation)
    assert eval_news2.tasks.mode == Mode.NEWS2
    assert eval_news2.tasks.budget_k is None
    assert eval_news2.assessments == []
    assert eval_news2.tasks.active == []

    patients, readings = build_ward(seed=42)
    assert isinstance(patients, list)
    assert isinstance(readings, list)

    sim = Simulator(seed=42)
    new_readings = sim.advance(to=now)
    assert isinstance(new_readings, list)
    sim.reset()


def test_health_endpoint():
    """Verify that GET /health returns status ok."""
    from starlette.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

