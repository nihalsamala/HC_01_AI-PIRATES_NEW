"""
WardPulse API routes.

Every endpoint from contracts.md section 8 with exact request/response models
from shared.schemas.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.db.models import AuditLogRow, FeedbackRow, PatientRow, TaskRow, VitalsRow
from app.db.session import get_db
from app.services import (
    _row_to_patient,
    _row_to_reading,
    _row_to_task,
    evaluate,
    event_bus,
    load_open_tasks,
    load_patients,
    load_vitals,
    persist_evaluation,
    run_evaluation_and_emit,
    sim_clock,
)
from shared.schemas import (
    AuditEntry,
    Consciousness,
    EvalResults,
    Mode,
    PatientAssessment,
    PatientDetail,
    SimControl,
    SimState,
    Source,
    StreamEvent,
    StreamEventType,
    Task,
    TaskFeedbackIn,
    TasksResponse,
    TaskStatus,
    VitalName,
    VitalsIn,
    VitalsReading,
    WardOverview,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /ward
# ---------------------------------------------------------------------------

@router.get("/ward")
def get_ward(db: Session = Depends(get_db)) -> WardOverview:
    """Get the ward overview (one WardBed per bed)."""
    evaluation = evaluate(db, Mode.WARDPULSE, sim_clock.sim_time)
    return evaluation.ward


# ---------------------------------------------------------------------------
# GET /patients/{id}
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientDetail:
    """Get patient details including recent vitals, assessment, and open tasks."""
    patient_row = db.query(PatientRow).filter(PatientRow.id == patient_id).first()
    if not patient_row:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    patient = _row_to_patient(patient_row)

    # Recent vitals (last 20 readings)
    vitals_rows = (
        db.query(VitalsRow)
        .filter(VitalsRow.patient_id == patient_id)
        .order_by(VitalsRow.timestamp.desc())
        .limit(20)
        .all()
    )
    recent_vitals = [_row_to_reading(r) for r in reversed(vitals_rows)]

    # Assessment from engine
    evaluation = evaluate(db, Mode.WARDPULSE, sim_clock.sim_time)
    assessment = next(
        (a for a in evaluation.assessments if a.patient_id == patient_id),
        None,
    )

    # Open tasks
    task_rows = db.query(TaskRow).filter(
        TaskRow.patient_id == patient_id,
        TaskRow.status.in_(["active", "queued"]),
    ).all()
    open_tasks = [_row_to_task(r) for r in task_rows]

    return PatientDetail(
        patient=patient,
        recent_vitals=recent_vitals,
        assessment=assessment,
        open_tasks=open_tasks,
    )


# ---------------------------------------------------------------------------
# GET /tasks?mode=wardpulse|news2
# ---------------------------------------------------------------------------

@router.get("/tasks")
def get_tasks(
    mode: Mode = Query(default=Mode.WARDPULSE),
    db: Session = Depends(get_db),
) -> TasksResponse:
    """Get task list for given mode."""
    evaluation = evaluate(db, mode, sim_clock.sim_time)
    return evaluation.tasks


# ---------------------------------------------------------------------------
# POST /vitals
# ---------------------------------------------------------------------------

@router.post("/vitals")
async def post_vitals(
    vitals_in: VitalsIn,
    db: Session = Depends(get_db),
) -> VitalsReading:
    """Submit a vital sign reading. timestamp=None uses sim_time."""
    # Validate patient exists
    patient_row = db.query(PatientRow).filter(PatientRow.id == vitals_in.patient_id).first()
    if not patient_row:
        raise HTTPException(status_code=404, detail=f"Patient {vitals_in.patient_id} not found")

    ts = vitals_in.timestamp if vitals_in.timestamp else sim_clock.sim_time

    row = VitalsRow(
        patient_id=vitals_in.patient_id,
        timestamp=ts,
        hr=vitals_in.hr,
        sbp=vitals_in.sbp,
        dbp=vitals_in.dbp,
        rr=vitals_in.rr,
        spo2=vitals_in.spo2,
        temp=vitals_in.temp,
        on_oxygen=vitals_in.on_oxygen,
        consciousness=vitals_in.consciousness.value if vitals_in.consciousness else "A",
        source=vitals_in.source.value if vitals_in.source else "manual",
    )
    db.add(row)

    # Audit
    db.add(AuditLogRow(
        timestamp=ts,
        event_type="vitals_entered",
        patient_id=vitals_in.patient_id,
        details={"source": vitals_in.source.value if vitals_in.source else "manual"},
    ))

    db.commit()
    db.refresh(row)

    reading = _row_to_reading(row)

    # Re-evaluate and emit
    await run_evaluation_and_emit(sim_clock.sim_time)

    return reading


# ---------------------------------------------------------------------------
# POST /tasks/{id}/done
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/done")
async def task_done(
    task_id: int,
    feedback: Optional[TaskFeedbackIn] = None,
    db: Session = Depends(get_db),
) -> Task:
    """Mark a task as done."""
    task_row = db.query(TaskRow).filter(TaskRow.id == task_id).first()
    if not task_row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task_row.status = "done"
    task_row.resolved_at = sim_clock.sim_time

    # Audit
    db.add(AuditLogRow(
        timestamp=sim_clock.sim_time,
        event_type="task_done",
        patient_id=task_row.patient_id,
        task_id=task_id,
        details={"note": feedback.note if feedback and feedback.note else ""},
    ))

    # Feedback
    if feedback:
        db.add(FeedbackRow(
            task_id=task_id,
            kind="done",
            note=feedback.note,
            timestamp=sim_clock.sim_time,
        ))

    db.commit()
    db.refresh(task_row)

    # Re-evaluate
    await run_evaluation_and_emit(sim_clock.sim_time)

    return _row_to_task(task_row)


# ---------------------------------------------------------------------------
# POST /tasks/{id}/not-useful
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/not-useful")
async def task_not_useful(
    task_id: int,
    feedback: Optional[TaskFeedbackIn] = None,
    db: Session = Depends(get_db),
) -> Task:
    """Mark a task as not useful (dismissed)."""
    task_row = db.query(TaskRow).filter(TaskRow.id == task_id).first()
    if not task_row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task_row.status = "dismissed"
    task_row.resolved_at = sim_clock.sim_time

    # Audit
    db.add(AuditLogRow(
        timestamp=sim_clock.sim_time,
        event_type="task_not_useful",
        patient_id=task_row.patient_id,
        task_id=task_id,
        details={"note": feedback.note if feedback and feedback.note else ""},
    ))

    # Feedback
    if feedback:
        db.add(FeedbackRow(
            task_id=task_id,
            kind="not_useful",
            note=feedback.note,
            timestamp=sim_clock.sim_time,
        ))

    db.commit()
    db.refresh(task_row)

    # Re-evaluate
    await run_evaluation_and_emit(sim_clock.sim_time)

    return _row_to_task(task_row)


# ---------------------------------------------------------------------------
# GET /sim/state
# ---------------------------------------------------------------------------

@router.get("/sim/state")
def get_sim_state() -> SimState:
    """Get current simulation state."""
    return sim_clock.get_state()


# ---------------------------------------------------------------------------
# POST /sim/control
# ---------------------------------------------------------------------------

@router.post("/sim/control")
async def post_sim_control(control: SimControl) -> SimState:
    """Control the simulation: play, pause, reset, set_speed."""
    if control.action == "play":
        return await sim_clock.play()
    elif control.action == "pause":
        return await sim_clock.pause()
    elif control.action == "reset":
        return await sim_clock.reset()
    elif control.action == "set_speed":
        return await sim_clock.set_speed(control.speed_minutes_per_second)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {control.action}")


# ---------------------------------------------------------------------------
# GET /stream (SSE)
# ---------------------------------------------------------------------------

@router.get("/stream")
async def stream_events():
    """Server-sent events stream using sse-starlette."""
    queue = event_bus.subscribe()

    async def event_generator():
        try:
            while True:
                event: StreamEvent = await queue.get()
                yield {
                    "event": event.type.value,
                    "data": event.model_dump_json(),
                }
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# GET /eval/results
# ---------------------------------------------------------------------------

@router.get("/eval/results")
def get_eval_results() -> EvalResults:
    """Read evaluation results from backend/evaluation/results.json if it exists."""
    results_path = Path(__file__).resolve().parent.parent.parent / "evaluation" / "results.json"
    if not results_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation results not available. Run `python -m evaluation.run_eval` first.",
        )
    with open(results_path, "r") as f:
        data = json.load(f)
    return EvalResults(**data)


# ---------------------------------------------------------------------------
# GET /audit?limit=100
# ---------------------------------------------------------------------------

@router.get("/audit")
def get_audit(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[AuditEntry]:
    """Get recent audit log entries."""
    rows = (
        db.query(AuditLogRow)
        .order_by(AuditLogRow.timestamp.desc())
        .limit(limit)
        .all()
    )
    results = []
    for r in rows:
        details = r.details if isinstance(r.details, dict) else json.loads(r.details or "{}")
        results.append(AuditEntry(
            id=r.id,
            timestamp=r.timestamp,
            event_type=r.event_type,
            patient_id=r.patient_id,
            task_id=r.task_id,
            details=details,
        ))
    return results
