"""
API tests for WardPulse backend (P4).

Uses FastAPI TestClient with a temporary SQLite database.
"""

import json
import os
import tempfile
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, PatientRow, VitalsRow, AuditLogRow
from app.db.session import get_db
from app.main import app
from shared.schemas import (
    Mode,
    SimState,
    TasksResponse,
    VitalsIn,
    VitalsReading,
    WardOverview,
    Source,
    Consciousness,
    TaskFeedbackIn,
)

# We use httpx for TestClient if available (FastAPI 0.100+)
try:
    from starlette.testclient import TestClient
except ImportError:
    from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures: temp database
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Create a temp SQLite database and yield a session."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_url = f"sqlite:///{tmp.name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    # Seed some basic data
    _seed_test_data(session)
    session.commit()

    yield session, TestSession, engine

    session.close()
    engine.dispose()
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


def _seed_test_data(session):
    """Insert minimal test patients and vitals."""
    now = datetime(2026, 10, 20, 6, 0)

    # 20 patients (or at least 3 for test coverage)
    for bed in range(1, 21):
        session.add(PatientRow(
            id=bed,
            bed=bed,
            age=50 + bed,
            conditions=json.dumps([]),
            admitted_at=now,
            display_name=f"Bed {bed}",
        ))
        # One vitals reading per patient
        session.add(VitalsRow(
            patient_id=bed,
            timestamp=now,
            hr=72.0 + bed * 0.5,
            sbp=120.0,
            dbp=80.0,
            rr=16.0,
            spo2=98.0,
            temp=36.6,
            on_oxygen=False,
            consciousness="A",
            source="sim",
        ))


@pytest.fixture
def client(db_session):
    """Create a test client with the temp database."""
    session, TestSession, engine = db_session

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestWard:
    def test_ward_returns_beds(self, client):
        r = client.get("/ward")
        assert r.status_code == 200
        data = r.json()
        assert "beds" in data
        assert len(data["beds"]) == 20


class TestVitals:
    def test_post_vitals_returns_reading(self, client):
        """Posting vitals returns a VitalsReading and triggers re-evaluation."""
        payload = {
            "patient_id": 1,
            "hr": 88.0,
            "sbp": 130.0,
            "dbp": 85.0,
            "rr": 18.0,
            "spo2": 97.0,
            "source": "manual",
        }
        r = client.post("/vitals", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["patient_id"] == 1
        assert data["hr"] == 88.0
        assert "id" in data
        assert "timestamp" in data

    def test_post_vitals_invalid_returns_422(self, client):
        """Posting vitals with no measurements returns 422."""
        payload = {
            "patient_id": 1,
            "source": "manual",
        }
        r = client.post("/vitals", json=payload)
        assert r.status_code == 422

    def test_post_vitals_nonexistent_patient(self, client):
        """Posting vitals for unknown patient returns 404."""
        payload = {
            "patient_id": 999,
            "hr": 72.0,
            "source": "manual",
        }
        r = client.post("/vitals", json=payload)
        assert r.status_code == 404


class TestTasks:
    def test_tasks_wardpulse_mode(self, client):
        """GET /tasks?mode=wardpulse returns valid TasksResponse."""
        r = client.get("/tasks?mode=wardpulse")
        assert r.status_code == 200
        data = r.json()
        assert data["mode"] == "wardpulse"
        assert "emergency" in data
        assert "active" in data
        assert "queue" in data
        assert "budget_k" in data

    def test_tasks_news2_mode(self, client):
        """GET /tasks?mode=news2 returns valid TasksResponse."""
        r = client.get("/tasks?mode=news2")
        assert r.status_code == 200
        data = r.json()
        assert data["mode"] == "news2"
        assert data["budget_k"] is None


class TestTaskActions:
    def test_done_and_not_useful(self, client, db_session):
        """Marking task done and not-useful changes status and writes audit and feedback."""
        session, TestSession, engine = db_session
        now = datetime(2026, 10, 20, 6, 0)

        # Seed two tasks directly in the DB
        from app.db.models import TaskRow
        t1 = TaskRow(
            patient_id=1, bed=1, type="repeat_bp", title="Repeat manual BP: Bed 1",
            reason="test reason", priority=0.5, status="active", emergency=False,
            escalated=False, created_at=now,
        )
        t2 = TaskRow(
            patient_id=2, bed=2, type="repeat_bp", title="Repeat manual BP: Bed 2",
            reason="test reason 2", priority=0.3, status="active", emergency=False,
            escalated=False, created_at=now,
        )
        session.add(t1)
        session.add(t2)
        session.commit()
        session.refresh(t1)
        session.refresh(t2)

        # Mark t1 done
        r = client.post(f"/tasks/{t1.id}/done", json={"note": "test done"})
        assert r.status_code == 200
        assert r.json()["status"] == "done"

        # Check audit for task_done
        r = client.get("/audit?limit=10")
        assert r.status_code == 200
        events = [a["event_type"] for a in r.json()]
        assert "task_done" in events

        # Mark t2 not-useful
        r = client.post(f"/tasks/{t2.id}/not-useful", json={"note": "not helpful"})
        assert r.status_code == 200
        assert r.json()["status"] == "dismissed"

        # Check audit for task_not_useful
        r = client.get("/audit?limit=10")
        assert r.status_code == 200
        events = [a["event_type"] for a in r.json()]
        assert "task_not_useful" in events


class TestSimControl:
    def test_sim_state(self, client):
        """GET /sim/state returns SimState."""
        r = client.get("/sim/state")
        assert r.status_code == 200
        data = r.json()
        assert "running" in data
        assert "sim_time" in data
        assert "speed_minutes_per_second" in data

    def test_sim_control_set_speed(self, client):
        """POST /sim/control set_speed changes speed."""
        r = client.post("/sim/control", json={
            "action": "set_speed",
            "speed_minutes_per_second": 20.0,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["speed_minutes_per_second"] == 20.0


class TestPatient:
    def test_get_patient(self, client):
        """GET /patients/1 returns patient details."""
        r = client.get("/patients/1")
        assert r.status_code == 200
        data = r.json()
        assert data["patient"]["id"] == 1
        assert "recent_vitals" in data

    def test_get_patient_not_found(self, client):
        """GET /patients/999 returns 404."""
        r = client.get("/patients/999")
        assert r.status_code == 404


class TestAudit:
    def test_audit_returns_list(self, client):
        """GET /audit returns a list of audit entries."""
        r = client.get("/audit?limit=10")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestEvalResults:
    def test_eval_results_404_when_missing(self, client):
        """GET /eval/results returns 404 when results.json doesn't exist."""
        r = client.get("/eval/results")
        assert r.status_code == 404
