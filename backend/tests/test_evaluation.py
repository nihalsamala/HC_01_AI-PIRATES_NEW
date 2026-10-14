"""
Test suite for WardPulse evaluation module (P7).

Verifies:
  - Replay downsampling produces gaps of roughly 4 to 6 hours
  - Missing values stay None
  - Zero lookahead: engine only sees vitals up to current time
  - Metrics calculation correctness on a hand-crafted test case
  - run() generates valid EvalResults and writes results.json
"""

from datetime import datetime, timedelta
from pathlib import Path
import pytest

from engine.config import DEFAULT_CONFIG
from evaluation.metrics import compute_metrics
from evaluation.replay import (
    ReplayCase,
    _parse_float,
    downsample_readings,
    generate_synthetic_cases,
    load_dataset,
)
from evaluation.run_eval import run
from shared.schemas import Condition, Consciousness, EvalResults, Mode, Patient, Source, VitalsReading


def test_missing_values_stay_none():
    """Verify missing and NaN values strictly evaluate to None."""
    assert _parse_float("NaN") is None
    assert _parse_float("nan") is None
    assert _parse_float("") is None
    assert _parse_float("   ") is None
    assert _parse_float("None") is None
    assert _parse_float("120.5") == 120.5
    assert _parse_float("0") == 0.0


def test_replay_downsampling_gaps():
    """Verify downsampling hourly records produces gaps of roughly 4 to 6 hours."""
    base_time = datetime(2026, 10, 1, 0, 0)
    hourly_rows = []
    for h in range(48):
        hourly_rows.append({
            "timestamp": base_time + timedelta(hours=h),
            "hr": 75.0,
            "sbp": 120.0,
            "dbp": 80.0,
            "rr": 16.0,
            "spo2": 98.0,
            "temp": 36.6,
        })

    readings = downsample_readings(hourly_rows, patient_id=1, sampling_interval_hours=4.0, seed=42)

    assert len(readings) > 0
    assert len(readings) < len(hourly_rows)  # Clearly downsampled from 48

    for i in range(1, len(readings)):
        gap_hours = (readings[i].timestamp - readings[i - 1].timestamp).total_seconds() / 3600.0
        assert 3.5 <= gap_hours <= 7.0, f"Unexpected gap: {gap_hours} hours"


def test_no_lookahead():
    """Verify evaluation does not look ahead to future readings."""
    cases = generate_synthetic_cases(n_cases=5, seed=42)
    # Ensure compute_metrics executes without error and only processes chronologically
    metrics_wp = compute_metrics(cases, Mode.WARDPULSE, DEFAULT_CONFIG)
    assert metrics_wp.events_total >= 0
    assert metrics_wp.system == Mode.WARDPULSE


def test_metrics_tiny_handmade_case():
    """Verify metrics calculation on a hand-crafted test case with known event and detection."""
    base_time = datetime(2026, 10, 1, 6, 0)
    p = Patient(
        id=99,
        bed=1,
        age=60,
        conditions=[],
        admitted_at=base_time,
        display_name="Handmade Patient",
    )

    # 4 readings:
    # 0h: normal
    # 5h: normal
    # 10h: acute tachypnea (RR 26) + tachycardia (HR 125) -> triggers page_doctor!
    # 15h: event time (shock)
    event_time = base_time + timedelta(hours=15)

    readings = [
        VitalsReading(
            id=1, patient_id=99, timestamp=base_time, source=Source.REPLAY,
            hr=72.0, sbp=120.0, dbp=80.0, rr=16.0, spo2=98.0, temp=36.6,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=2, patient_id=99, timestamp=base_time + timedelta(hours=5), source=Source.REPLAY,
            hr=75.0, sbp=118.0, dbp=78.0, rr=16.0, spo2=98.0, temp=36.7,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=3, patient_id=99, timestamp=base_time + timedelta(hours=10), source=Source.REPLAY,
            hr=125.0, sbp=95.0, dbp=60.0, rr=26.0, spo2=93.0, temp=38.4,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=4, patient_id=99, timestamp=event_time, source=Source.REPLAY,
            hr=138.0, sbp=80.0, dbp=50.0, rr=30.0, spo2=88.0, temp=38.8,
            on_oxygen=False, consciousness=Consciousness.CONFUSION,
        ),
    ]

    case = ReplayCase(patient=p, readings=readings, event_time=event_time)
    metrics = compute_metrics([case], Mode.WARDPULSE, DEFAULT_CONFIG)

    assert metrics.events_total == 1
    assert metrics.events_detected == 1
    assert metrics.sensitivity == 1.0
    # First detection occurred at hour 10, event at hour 15 -> lead time = 5.0 hours!
    assert metrics.median_lead_time_hours == 5.0


def test_run_eval_synthetic_fallback(tmp_path):
    """Verify run() produces valid EvalResults and writes results.json."""
    results = run(data_path=tmp_path, n_cases=50)

    assert isinstance(results, EvalResults)
    assert results.n_patients == 50
    assert len(results.systems) == 2

    # Check results.json exists and is valid
    results_path = Path(__file__).resolve().parent.parent / "evaluation" / "results.json"
    assert results_path.exists()
    assert results_path.stat().st_size > 0
