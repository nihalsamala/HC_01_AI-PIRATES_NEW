"""
Test suite for WardPulse simulator, clock, and scenarios.
"""

from datetime import timedelta
import pytest

from shared.schemas import Patient, VitalsIn, VitalsReading
from simulator.clock import Simulator
from simulator.scenarios import (
    DELIBERATELY_MISSED_READINGS,
    SIM_START,
)
from simulator.ward import build_ward


def test_20_patients_created():
    """Verify exactly 20 patients are created with beds 1 to 20 and varied ages."""
    patients, readings = build_ward(seed=42)
    assert len(patients) == 20
    assert len(readings) > 0

    bed_numbers = [p.bed for p in patients]
    assert sorted(bed_numbers) == list(range(1, 21))

    for p in patients:
        assert isinstance(p, Patient)
        assert p.display_name == f"Bed {p.bed}"
        assert 0 <= p.age <= 120

    ages = [p.age for p in patients]
    assert min(ages) < 40
    assert max(ages) > 70


def test_determinism():
    """Same seed must produce identical outputs; different seeds must differ."""
    patients1, readings1 = build_ward(seed=42)
    patients2, readings2 = build_ward(seed=42)
    patients3, readings3 = build_ward(seed=999)

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

    # Different seed gives different values / jitter
    assert readings1 != readings3

    # Simulator determinism
    sim1 = Simulator(seed=42)
    sim2 = Simulator(seed=42)
    sim_diff = Simulator(seed=999)

    adv1 = sim1.advance(SIM_START + timedelta(hours=3))
    adv2 = sim2.advance(SIM_START + timedelta(hours=3))
    adv_diff = sim_diff.advance(SIM_START + timedelta(hours=3))

    assert adv1 == adv2
    assert adv1 != adv_diff


def test_bed_3_history_rr_between_20_and_24():
    """Bed 3 COPD history RR must all be strictly between 20 and 24."""
    patients, readings = build_ward(seed=42)
    bed3_readings = [r for r in readings if r.patient_id == 3]

    assert len(bed3_readings) >= 4
    for r in bed3_readings:
        assert r.rr is not None
        assert 20.0 <= r.rr <= 24.0
        assert r.spo2 is not None
        assert 90.0 <= r.spo2 <= 92.0


def test_bed_7_rr_at_sim_start_plus_1h_equals_22():
    """Bed 7 latest RR in history or at SIM_START + 1h equals 22."""
    patients, readings = build_ward(seed=42)
    bed7_history = [r for r in readings if r.patient_id == 7]
    assert len(bed7_history) >= 4

    # Early history was normal, rising gently
    assert bed7_history[0].rr == 14.0

    sim = Simulator(seed=42)
    advance_events = sim.advance(SIM_START + timedelta(hours=1))
    bed7_adv = [e for e in advance_events if e.patient_id == 7]

    assert len(bed7_adv) >= 1
    assert bed7_adv[-1].rr == 22.0
    assert bed7_adv[-1].hr == 98.0


def test_bed_4_last_sbp_at_least_7h_before_sim_start_plus_3h():
    """Bed 4 last SBP reading must be at least 7 hours old at SIM_START + 3h."""
    patients, readings = build_ward(seed=42)
    t_target = SIM_START + timedelta(hours=3)

    sim = Simulator(seed=42)
    adv_readings = sim.advance(t_target)

    # Collect all readings up to SIM_START + 3h for Bed 4
    bed4_readings = [r for r in readings if r.patient_id == 4 and r.sbp is not None]
    bed4_adv = [e for e in adv_readings if e.patient_id == 4 and e.sbp is not None]

    all_sbp_readings = bed4_readings + bed4_adv
    assert len(all_sbp_readings) > 0

    latest_sbp_reading = max(all_sbp_readings, key=lambda r: r.timestamp)
    time_diff = t_target - latest_sbp_reading.timestamp
    assert time_diff >= timedelta(hours=7)

    # Also verify that other vitals were taken more recently
    bed4_other_recent = [
        r for r in readings
        if r.patient_id == 4 and r.timestamp >= SIM_START - timedelta(hours=2)
    ]
    assert len(bed4_other_recent) >= 1
    assert bed4_other_recent[0].sbp is None
    assert bed4_other_recent[0].hr is not None


def test_at_least_3_missed_scheduled_readings():
    """At least 3 scheduled readings across the ward are deliberately missed."""
    patients, readings = build_ward(seed=42)
    assert len(DELIBERATELY_MISSED_READINGS) >= 3

    for missed in DELIBERATELY_MISSED_READINGS:
        bed = missed["bed"]
        sched_time = missed["scheduled_time"]
        # Confirm no reading exists within 30 minutes of scheduled time
        matching = [
            r for r in readings
            if r.patient_id == bed and abs((r.timestamp - sched_time).total_seconds()) < 1800
        ]
        assert len(matching) == 0, f"Expected missed reading for Bed {bed} at {sched_time}"


def test_bed_12_crash_appears_only_after_sim_start_plus_5h():
    """The Bed 12 crash reading must appear only after SIM_START + 5h."""
    patients, readings = build_ward(seed=42)
    bed12_history = [r for r in readings if r.patient_id == 12]
    for r in bed12_history:
        assert r.sbp > 100
        assert r.hr < 100
        assert r.spo2 > 95

    sim = Simulator(seed=42)
    # Advance up to 4h 59m
    events_before = sim.advance(SIM_START + timedelta(hours=4, minutes=59))
    bed12_before = [e for e in events_before if e.patient_id == 12]
    for e in bed12_before:
        assert e.sbp > 100
        assert e.hr < 100

    # Advance to 5h
    events_at_5h = sim.advance(SIM_START + timedelta(hours=5))
    bed12_crash = [e for e in events_at_5h if e.patient_id == 12]
    assert len(bed12_crash) == 1
    crash = bed12_crash[0]
    assert crash.sbp == 78.0
    assert crash.hr == 135.0
    assert crash.spo2 == 86.0
    assert crash.rr == 28.0


def test_advance_never_returns_readings_before_cursor():
    """advance() never returns readings before the previous cursor."""
    sim = Simulator(seed=42)
    t1 = SIM_START + timedelta(hours=1)
    readings1 = sim.advance(t1)
    for r in readings1:
        assert SIM_START < r.timestamp <= t1

    # Calling with past or current time returns empty
    assert sim.advance(SIM_START) == []
    assert sim.advance(t1) == []

    # Calling with future time returns only events strictly after t1
    t2 = SIM_START + timedelta(hours=3)
    readings2 = sim.advance(t2)
    for r in readings2:
        assert t1 < r.timestamp <= t2


def test_all_outputs_validate_against_schemas():
    """All simulator outputs must validate strictly against shared.schemas."""
    patients, readings = build_ward(seed=42)

    for p in patients:
        assert isinstance(p, Patient)
        assert p.bed >= 1

    for r in readings:
        assert isinstance(r, VitalsReading)
        if r.sbp is not None and r.dbp is not None:
            assert r.sbp >= r.dbp
        assert len(r.measured()) > 0

    sim = Simulator(seed=42)
    adv_events = sim.advance(SIM_START + timedelta(hours=6))
    for e in adv_events:
        assert isinstance(e, VitalsIn)
        if e.sbp is not None and e.dbp is not None:
            assert e.sbp >= e.dbp
        assert len(e.measured()) > 0

    # Test reset restores simulator
    sim.reset()
    assert sim.current_time == SIM_START
    adv_after_reset = sim.advance(SIM_START + timedelta(hours=6))
    assert adv_events == adv_after_reset
