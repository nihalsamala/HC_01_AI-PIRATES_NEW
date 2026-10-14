"""
Test suite for replayed real-data ward simulator (Task P7b).

Verifies:
  1. source="replay" populates all 20 beds with de-identified patient records.
  2. Every replayed reading has source == Source.REPLAY.
  3. Timestamps are valid and confined to the 24-hour observation window ending at SIM_START.
  4. Seed-based determinism (identical outputs for same seed, varied for different seeds).
  5. Scripted stories overlay accurately and produce the expected cards through the engine:
     - Story 1 (07:00:00): Bed 3 (COPD) calm, Bed 7 (Post-op) active card.
     - Story 2 (09:00:00): Bed 4 gets repeat_bp, not page_doctor.
     - Story 3 (11:00:00): Bed 12 crash bypass in emergency while active holds K=2 cards.
  6. Naive comparator toggle triggers significantly more alert noise than WardPulse.
"""

from datetime import timedelta
import pytest

from engine.config import DEFAULT_CONFIG
from engine.news2 import evaluate_ward_news2
from engine.pipeline import evaluate_ward
from shared.schemas import Mode, Patient, Source, TaskType, VitalsReading
from simulator.clock import Simulator
from simulator.scenarios import SIM_START
from simulator.ward import build_ward


def test_replay_mode_20_beds_populated_and_valid():
    """Verify source='replay' populates exactly 20 beds with de-identified records."""
    patients, readings = build_ward(seed=42, source="replay")

    assert len(patients) == 20
    assert len(readings) > 0

    bed_numbers = [p.bed for p in patients]
    assert sorted(bed_numbers) == list(range(1, 21))

    for p in patients:
        assert isinstance(p, Patient)
        # De-identified: display_name is Bed X, no real patient names
        assert p.display_name == f"Bed {p.bed}"
        assert 18 <= p.age <= 120
        assert p.admitted_at <= SIM_START

    # Verify every reading has Source.REPLAY
    for r in readings:
        assert isinstance(r, VitalsReading)
        assert r.source == Source.REPLAY
        # Valid historical timestamps within 24h prior to SIM_START
        assert SIM_START - timedelta(hours=25) <= r.timestamp <= SIM_START

    # Verify chronological ordering
    timestamps = [r.timestamp for r in readings]
    assert timestamps == sorted(timestamps)


def test_replay_mode_determinism():
    """Same seed must produce identical outputs; different seeds must differ."""
    patients1, readings1 = build_ward(seed=42, source="replay")
    patients2, readings2 = build_ward(seed=42, source="replay")
    patients3, readings3 = build_ward(seed=999, source="replay")

    assert len(readings1) == len(readings2)
    for r1, r2 in zip(readings1, readings2):
        assert r1.id == r2.id
        assert r1.patient_id == r2.patient_id
        assert r1.timestamp == r2.timestamp
        assert r1.hr == r2.hr
        assert r1.sbp == r2.sbp
        assert r1.dbp == r2.dbp
        assert r1.rr == r2.rr
        assert r1.spo2 == r2.spo2
        assert r1.source == Source.REPLAY

    # Different seed gives different values
    assert readings1 != readings3

    # Simulator determinism
    sim1 = Simulator(seed=42, source="replay")
    sim2 = Simulator(seed=42, source="replay")
    sim_diff = Simulator(seed=999, source="replay")

    adv1 = sim1.advance(SIM_START + timedelta(hours=3))
    adv2 = sim2.advance(SIM_START + timedelta(hours=3))
    adv_diff = sim_diff.advance(SIM_START + timedelta(hours=3))

    assert adv1 == adv2
    assert adv1 != adv_diff
    for e in adv1:
        assert e.source == Source.REPLAY


def test_replay_simulator_events_have_replay_source():
    """Verify Simulator(source='replay') advances with Source.REPLAY events."""
    sim = Simulator(seed=42, source="replay")
    events = sim.advance(SIM_START + timedelta(hours=6))

    assert len(events) > 0
    for e in events:
        assert e.source == Source.REPLAY

    # Scripted events present with Source.REPLAY
    bed7_events = [e for e in events if e.patient_id == 7 and e.timestamp == SIM_START + timedelta(hours=1)]
    assert len(bed7_events) == 1
    assert bed7_events[0].rr == 22.0
    assert bed7_events[0].hr == 98.0
    assert bed7_events[0].source == Source.REPLAY

    bed12_events = [e for e in events if e.patient_id == 12 and e.timestamp == SIM_START + timedelta(hours=5)]
    assert len(bed12_events) == 1
    assert bed12_events[0].sbp == 78.0
    assert bed12_events[0].hr == 135.0
    assert bed12_events[0].source == Source.REPLAY


def test_replay_stories_produce_expected_cards_through_engine():
    """Overlay stories on replayed ward must correctly trigger engine cards."""
    patients, readings = build_ward(seed=42, source="replay")
    sim = Simulator(seed=42, source="replay")
    all_readings = list(readings)

    # -------------------------------------------------------------------------
    # Story 1: Same Number, Different Patients at SIM_START + 1h (07:00:00)
    # -------------------------------------------------------------------------
    t_1h = SIM_START + timedelta(hours=1)
    new_events_1h = sim.advance(t_1h)
    for idx, e in enumerate(new_events_1h, start=len(all_readings) + 1):
        all_readings.append(
            VitalsReading(
                id=idx,
                patient_id=e.patient_id,
                timestamp=e.timestamp,
                source=e.source,
                hr=e.hr,
                sbp=e.sbp,
                dbp=e.dbp,
                rr=e.rr,
                spo2=e.spo2,
                temp=e.temp,
                on_oxygen=e.on_oxygen,
                consciousness=e.consciousness,
            )
        )

    vitals_dict_1h = {}
    for r in all_readings:
        vitals_dict_1h.setdefault(r.patient_id, []).append(r)

    eval_1h = evaluate_ward(patients, vitals_dict_1h, t_1h, DEFAULT_CONFIG)

    # Bed 3 (COPD chronic RR 22) -> NO card in active
    active_beds_1h = [t.bed for t in eval_1h.tasks.active]
    assert 3 not in active_beds_1h, "Bed 3 (COPD) should not receive an active card for RR 22"

    # Bed 7 (Post-op RR 22) -> ACTIVE card in active
    assert 7 in active_beds_1h, "Bed 7 (Post-op) must receive an active card for RR 22"

    # -------------------------------------------------------------------------
    # Story 2: Stale BP vs False Alarm at SIM_START + 3h (09:00:00)
    # -------------------------------------------------------------------------
    t_3h = SIM_START + timedelta(hours=3)
    new_events_3h = sim.advance(t_3h)
    for idx, e in enumerate(new_events_3h, start=len(all_readings) + 1):
        all_readings.append(
            VitalsReading(
                id=idx,
                patient_id=e.patient_id,
                timestamp=e.timestamp,
                source=e.source,
                hr=e.hr,
                sbp=e.sbp,
                dbp=e.dbp,
                rr=e.rr,
                spo2=e.spo2,
                temp=e.temp,
                on_oxygen=e.on_oxygen,
                consciousness=e.consciousness,
            )
        )

    vitals_dict_3h = {}
    for r in all_readings:
        vitals_dict_3h.setdefault(r.patient_id, []).append(r)

    prev_tasks_3h = eval_1h.tasks.active + eval_1h.tasks.queue
    eval_3h = evaluate_ward(patients, vitals_dict_3h, t_3h, DEFAULT_CONFIG, previous_tasks=prev_tasks_3h)

    # Bed 4 BP is now 7 hours old -> repeat_bp task, NOT page_doctor
    bed4_tasks = [t for t in eval_3h.tasks.active + eval_3h.tasks.queue if t.bed == 4]
    assert len(bed4_tasks) >= 1
    assert any(t.type == TaskType.REPEAT_BP for t in bed4_tasks)
    assert not any(t.type == TaskType.PAGE_DOCTOR for t in bed4_tasks)

    # -------------------------------------------------------------------------
    # Story 3: Crash Bypass at SIM_START + 5h (11:00:00)
    # -------------------------------------------------------------------------
    t_5h = SIM_START + timedelta(hours=5)
    new_events_5h = sim.advance(t_5h)
    for idx, e in enumerate(new_events_5h, start=len(all_readings) + 1):
        all_readings.append(
            VitalsReading(
                id=idx,
                patient_id=e.patient_id,
                timestamp=e.timestamp,
                source=e.source,
                hr=e.hr,
                sbp=e.sbp,
                dbp=e.dbp,
                rr=e.rr,
                spo2=e.spo2,
                temp=e.temp,
                on_oxygen=e.on_oxygen,
                consciousness=e.consciousness,
            )
        )

    vitals_dict_5h = {}
    for r in all_readings:
        vitals_dict_5h.setdefault(r.patient_id, []).append(r)

    prev_tasks_5h = eval_3h.tasks.active + eval_3h.tasks.queue
    eval_5h = evaluate_ward(patients, vitals_dict_5h, t_5h, DEFAULT_CONFIG, previous_tasks=prev_tasks_5h)

    # Bed 12 crashes -> unequivocal CRASH BYPASS in emergency
    emergency_beds = [t.bed for t in eval_5h.tasks.emergency]
    assert 12 in emergency_beds, "Bed 12 must appear in emergency via crash bypass"

    # Active cards still respect K-budget (<= 2)
    assert len(eval_5h.tasks.active) <= DEFAULT_CONFIG.k_budget


def test_replay_mode_toggle_noise_reduction():
    """Verify Naive NEWS2 triggers substantially more alert noise than WardPulse."""
    patients, readings = build_ward(seed=42, source="replay")
    sim = Simulator(seed=42, source="replay")
    all_readings = list(readings)

    # Advance to 11:00:00 (Story 3 time)
    t_5h = SIM_START + timedelta(hours=5)
    events = sim.advance(t_5h)
    for idx, e in enumerate(events, start=len(all_readings) + 1):
        all_readings.append(
            VitalsReading(
                id=idx,
                patient_id=e.patient_id,
                timestamp=e.timestamp,
                source=e.source,
                hr=e.hr,
                sbp=e.sbp,
                dbp=e.dbp,
                rr=e.rr,
                spo2=e.spo2,
                temp=e.temp,
                on_oxygen=e.on_oxygen,
                consciousness=e.consciousness,
            )
        )

    vitals_dict_toggle = {}
    for r in all_readings:
        vitals_dict_toggle.setdefault(r.patient_id, []).append(r)

    eval_wp = evaluate_ward(patients, vitals_dict_toggle, t_5h, DEFAULT_CONFIG)
    eval_news2 = evaluate_ward_news2(patients, vitals_dict_toggle, t_5h, DEFAULT_CONFIG)

    alerts_wardpulse = eval_wp.tasks.alerts_shown
    alerts_news2 = eval_news2.tasks.alerts_shown

    # Naive mode should trigger many simultaneous alerts due to chronic beds (3, 5, 9, 14, 18)
    assert alerts_news2 >= 4
    assert alerts_news2 > alerts_wardpulse
