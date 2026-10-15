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
    """Verify evaluation strictly uses only readings up to decision time (zero lookahead)."""
    base_time = datetime(2026, 10, 1, 6, 0)
    p = Patient(
        id=101,
        bed=2,
        age=50,
        conditions=[],
        admitted_at=base_time,
        display_name="Lookahead Patient",
    )
    # Reading 1 (0h): Normal
    # Reading 2 (4h): Normal
    # Reading 3 (8h): Catastrophic shock (crash)
    readings = [
        VitalsReading(
            id=1, patient_id=101, timestamp=base_time, source=Source.REPLAY,
            hr=72.0, sbp=120.0, dbp=80.0, rr=16.0, spo2=98.0, temp=36.6,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=2, patient_id=101, timestamp=base_time + timedelta(hours=4), source=Source.REPLAY,
            hr=74.0, sbp=118.0, dbp=78.0, rr=16.0, spo2=98.0, temp=36.7,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=3, patient_id=101, timestamp=base_time + timedelta(hours=8), source=Source.REPLAY,
            hr=145.0, sbp=68.0, dbp=40.0, rr=32.0, spo2=82.0, temp=39.5,
            on_oxygen=False, consciousness=Consciousness.CONFUSION,
        ),
    ]
    # At t = 4h, evaluation must ONLY see readings 1 and 2, which are completely normal
    case = ReplayCase(patient=p, readings=readings, event_time=base_time + timedelta(hours=8))
    metrics_wp = compute_metrics([case], Mode.WARDPULSE, DEFAULT_CONFIG)
    assert metrics_wp.events_total == 1
    # First detection happens at hour 8 (when reading 3 occurs), NOT at hour 4
    assert metrics_wp.events_detected == 1
    assert metrics_wp.median_lead_time_hours == 0.0


def test_psv_unit_mapping_and_event_time(tmp_path):
    """Verify PhysioNet PSV header mapping, units, NaN handling, and event time = first label_1 + 6h."""
    from evaluation.replay import parse_psv_patient
    psv_content = (
        "HR|O2Sat|Temp|SBP|MAP|DBP|Resp|Age|Gender|Unit1|Unit2|HospAdmTime|ICULOS|SepsisLabel\n"
        "82|97|36.8|124|88|76|18|65|1|0|1|-0.03|1|0\n"
        "NaN|NaN|NaN|NaN|NaN|NaN|NaN|65|1|0|1|-0.03|2|0\n"
        "95|94|37.5|110|75|68|22|65|1|0|1|-0.03|3|1\n"
        "105|92|38.1|102|70|62|24|65|1|0|1|-0.03|4|1\n"
    )
    psv_file = tmp_path / "test_patient.psv"
    psv_file.write_text(psv_content, encoding="utf-8")

    patient, rows, event_time = parse_psv_patient(psv_file, patient_id=1)

    assert patient.age == 65
    assert len(rows) == 4

    # Row 0: Full vitals mapping
    r0 = rows[0]
    assert r0["hr"] == 82.0   # HR -> hr
    assert r0["spo2"] == 97.0 # O2Sat -> spo2
    assert r0["temp"] == 36.8 # Temp -> temp
    assert r0["sbp"] == 124.0 # SBP -> sbp
    assert r0["dbp"] == 76.0  # DBP -> dbp
    assert r0["rr"] == 18.0   # Resp -> rr

    # Row 1: NaNs become None
    r1 = rows[1]
    assert r1["hr"] is None
    assert r1["spo2"] is None
    assert r1["temp"] is None
    assert r1["sbp"] is None
    assert r1["dbp"] is None
    assert r1["rr"] is None

    # Event time check: first SepsisLabel=1 is at row index 2 (hour offset 2)
    # event_time must be timestamp of row 2 PLUS 6 hours!
    t_label1 = rows[2]["timestamp"]
    assert event_time == t_label1 + timedelta(hours=6)


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
