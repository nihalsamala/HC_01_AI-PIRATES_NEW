"""
WardPulse re-evaluation service and simulation clock.

The service layer sits between the API routes and the engine/simulator.
It handles:
  - Loading patients and vitals from the DB
  - Calling evaluate_ward / evaluate_ward_news2
  - Persisting resulting tasks (create, update, close)
  - Writing audit entries
  - Running the simulation clock as an asyncio background task
  - Emitting SSE events
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.models import AuditLogRow, FeedbackRow, PatientRow, TaskRow, VitalsRow
from app.db.session import SessionLocal
from engine.config import DEFAULT_CONFIG
from shared.schemas import (
    Condition,
    Consciousness,
    EngineConfig,
    Mode,
    Patient,
    PatientAssessment,
    RiskTier,
    SimControl,
    SimState,
    Source,
    StreamEvent,
    StreamEventType,
    Task,
    TasksResponse,
    TaskStatus,
    TaskType,
    VitalName,
    VitalsIn,
    VitalsReading,
    WardBed,
    WardEvaluation,
    WardOverview,
)
from simulator.scenarios import SIM_START


# ---------------------------------------------------------------------------
# SSE event bus (simple in-memory broadcast)
# ---------------------------------------------------------------------------

class EventBus:
    """Simple async event bus for SSE broadcasting."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def publish(self, event: StreamEvent) -> None:
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # Drop events for slow consumers


event_bus = EventBus()


# ---------------------------------------------------------------------------
# DB <-> Schema converters
# ---------------------------------------------------------------------------

def _row_to_patient(row: PatientRow) -> Patient:
    conds = row.conditions if isinstance(row.conditions, list) else json.loads(row.conditions or "[]")
    return Patient(
        id=row.id,
        bed=row.bed,
        age=row.age,
        conditions=[Condition(c) for c in conds],
        admitted_at=row.admitted_at,
        display_name=row.display_name,
    )


def _row_to_reading(row: VitalsRow) -> VitalsReading:
    return VitalsReading(
        id=row.id,
        patient_id=row.patient_id,
        timestamp=row.timestamp,
        hr=row.hr,
        sbp=row.sbp,
        dbp=row.dbp,
        rr=row.rr,
        spo2=row.spo2,
        temp=row.temp,
        on_oxygen=row.on_oxygen,
        consciousness=Consciousness(row.consciousness) if row.consciousness else Consciousness.ALERT,
        source=Source(row.source) if row.source else Source.SIM,
    )


def _row_to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        patient_id=row.patient_id,
        bed=row.bed,
        type=TaskType(row.type),
        target_vital=VitalName(row.target_vital) if row.target_vital else None,
        title=row.title,
        reason=row.reason,
        priority=row.priority,
        status=TaskStatus(row.status),
        emergency=row.emergency,
        escalated=row.escalated,
        created_at=row.created_at,
        waiting_minutes=row.waiting_minutes if hasattr(row, 'waiting_minutes') else 0.0,
        resolved_at=row.resolved_at,
    )


def _task_to_row(task: Task) -> TaskRow:
    return TaskRow(
        patient_id=task.patient_id,
        bed=task.bed,
        type=task.type.value,
        target_vital=task.target_vital.value if task.target_vital else None,
        title=task.title,
        reason=task.reason,
        priority=task.priority,
        status=task.status.value,
        emergency=task.emergency,
        escalated=task.escalated,
        created_at=task.created_at,
        resolved_at=task.resolved_at,
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_patients(db: Session) -> List[Patient]:
    rows = db.query(PatientRow).order_by(PatientRow.bed).all()
    return [_row_to_patient(r) for r in rows]


def load_vitals(db: Session, up_to: Optional[datetime] = None) -> Dict[int, List[VitalsReading]]:
    query = db.query(VitalsRow)
    if up_to is not None:
        query = query.filter(VitalsRow.timestamp <= up_to)
    rows = query.order_by(VitalsRow.timestamp).all()
    result: Dict[int, List[VitalsReading]] = {}
    for r in rows:
        reading = _row_to_reading(r)
        result.setdefault(reading.patient_id, []).append(reading)
    return result


def load_open_tasks(db: Session) -> List[Task]:
    rows = db.query(TaskRow).filter(
        TaskRow.status.in_(["active", "queued"])
    ).all()
    return [_row_to_task(r) for r in rows]


# ---------------------------------------------------------------------------
# Re-evaluation
# ---------------------------------------------------------------------------

def evaluate(db: Session, mode: Mode, sim_time: datetime) -> WardEvaluation:
    """Run the engine and return evaluation results."""
    patients = load_patients(db)
    vitals = load_vitals(db, up_to=sim_time)
    previous_tasks = load_open_tasks(db)

    from engine.pipeline import evaluate_ward
    from engine.news2 import evaluate_ward_news2

    config = DEFAULT_CONFIG

    if mode == Mode.WARDPULSE:
        result = evaluate_ward(patients, vitals, sim_time, config, previous_tasks)
    else:
        result = evaluate_ward_news2(patients, vitals, sim_time, config, previous_tasks=None)

    return result


def persist_evaluation(db: Session, evaluation: WardEvaluation, sim_time: datetime) -> None:
    """Persist tasks from an evaluation into the database.
    
    - Creates new tasks that don't exist yet
    - Updates existing open tasks (priority, status, escalated)
    - Closes tasks whose condition cleared (not in new results)
    """
    # Get all engine-generated tasks
    all_new_tasks = (
        list(evaluation.tasks.emergency) +
        list(evaluation.tasks.active) +
        list(evaluation.tasks.queue)
    )

    # Load current open tasks from DB
    existing_rows = db.query(TaskRow).filter(
        TaskRow.status.in_(["active", "queued"])
    ).all()
    existing_by_key = {(r.patient_id, r.type): r for r in existing_rows}

    seen_keys = set()

    for task in all_new_tasks:
        key = (task.patient_id, task.type.value)
        seen_keys.add(key)

        if key in existing_by_key:
            # Update existing task
            row = existing_by_key[key]
            row.priority = task.priority
            row.status = task.status.value
            row.emergency = task.emergency
            row.escalated = task.escalated
        else:
            # Create new task
            new_row = _task_to_row(task)
            db.add(new_row)
            db.flush()  # Get the ID

            # Audit
            db.add(AuditLogRow(
                timestamp=sim_time,
                event_type="task_created",
                patient_id=task.patient_id,
                task_id=new_row.id,
                details={"type": task.type.value, "priority": task.priority},
            ))

            if task.emergency:
                db.add(AuditLogRow(
                    timestamp=sim_time,
                    event_type="crash_bypass",
                    patient_id=task.patient_id,
                    task_id=new_row.id,
                    details={"reason": task.reason},
                ))

    # Close tasks whose condition cleared
    for key, row in existing_by_key.items():
        if key not in seen_keys:
            row.status = "done"
            row.resolved_at = sim_time

    db.commit()


async def run_evaluation_and_emit(sim_time: datetime) -> None:
    """Re-evaluate in WardPulse mode, persist, and emit SSE events."""
    db = SessionLocal()
    try:
        evaluation = evaluate(db, Mode.WARDPULSE, sim_time)
        persist_evaluation(db, evaluation, sim_time)

        # Emit events
        await event_bus.publish(StreamEvent(
            type=StreamEventType.TASKS_UPDATED,
            timestamp=sim_time,
        ))
        await event_bus.publish(StreamEvent(
            type=StreamEventType.WARD_UPDATED,
            timestamp=sim_time,
        ))

        # Check for emergency
        if evaluation.tasks.emergency:
            await event_bus.publish(StreamEvent(
                type=StreamEventType.EMERGENCY,
                timestamp=sim_time,
                data={"count": len(evaluation.tasks.emergency)},
            ))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Simulation clock state
# ---------------------------------------------------------------------------

class SimClock:
    """Manages simulation state and the background clock task."""

    def __init__(self):
        self.running: bool = False
        self.speed_minutes_per_second: float = 10.0
        self.sim_time: datetime = SIM_START
        self.start_time: datetime = SIM_START
        self._task: Optional[asyncio.Task] = None
        self._simulator = None

    def _get_simulator(self):
        if self._simulator is None:
            from simulator.clock import Simulator
            self._simulator = Simulator(seed=42)
        return self._simulator

    def get_state(self) -> SimState:
        return SimState(
            running=self.running,
            speed_minutes_per_second=self.speed_minutes_per_second,
            sim_time=self.sim_time,
            start_time=self.start_time,
            scenario="default",
        )

    async def play(self) -> SimState:
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._tick_loop())
        return self.get_state()

    async def pause(self) -> SimState:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        return self.get_state()

    async def reset(self) -> SimState:
        await self.pause()
        self.sim_time = SIM_START
        self.start_time = SIM_START

        # Reseed DB
        from app.db.seed import seed_db
        seed_db()

        # Reset simulator
        sim = self._get_simulator()
        sim.reset()

        return self.get_state()

    async def set_speed(self, speed: float) -> SimState:
        self.speed_minutes_per_second = speed
        return self.get_state()

    async def _tick_loop(self) -> None:
        """Background loop: advances sim_time and processes readings each tick."""
        sim = self._get_simulator()
        tick_interval = 0.5  # real seconds between ticks

        while self.running:
            try:
                await asyncio.sleep(tick_interval)
                if not self.running:
                    break

                # Advance sim time
                delta_minutes = self.speed_minutes_per_second * tick_interval
                self.sim_time += timedelta(minutes=delta_minutes)

                # Get new readings from simulator
                new_readings = sim.advance(self.sim_time)

                if new_readings:
                    # Store new readings
                    db = SessionLocal()
                    try:
                        for vi in new_readings:
                            ts = vi.timestamp if vi.timestamp else self.sim_time
                            db.add(VitalsRow(
                                patient_id=vi.patient_id,
                                timestamp=ts,
                                hr=vi.hr,
                                sbp=vi.sbp,
                                dbp=vi.dbp,
                                rr=vi.rr,
                                spo2=vi.spo2,
                                temp=vi.temp,
                                on_oxygen=vi.on_oxygen,
                                consciousness=vi.consciousness.value if vi.consciousness else "A",
                                source=vi.source.value if vi.source else "sim",
                            ))

                            db.add(AuditLogRow(
                                timestamp=ts,
                                event_type="vitals_entered",
                                patient_id=vi.patient_id,
                                details={"source": "sim"},
                            ))
                        db.commit()
                    finally:
                        db.close()

                    # Re-evaluate
                    await run_evaluation_and_emit(self.sim_time)

                # Emit sim tick
                await event_bus.publish(StreamEvent(
                    type=StreamEventType.SIM_TICK,
                    timestamp=self.sim_time,
                    data=self.get_state().model_dump(mode="json"),
                ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but don't crash the tick loop
                print(f"Tick error: {e}")
                continue


# Global singleton
sim_clock = SimClock()
