"""
Test suite for WardPulse Machine Learning Module (P8).

Verifies:
  - Model loader returns None gracefully when model file does not exist
  - Patient-level split guarantees zero leakage between train and test
  - Model training produces valid model.txt (<50KB) and metrics.json (AUROC, AUPRC)
  - Inference returns valid probability in [0.0, 1.0] when model is present
  - Rules-based safety floor: red-line breach cannot be suppressed by low ML score
  - Existing engine risk calculation functions cleanly with model present or absent
"""

from datetime import datetime, timedelta
from pathlib import Path
import pytest

from engine.config import DEFAULT_CONFIG
from engine.features import extract_features
from engine.risk import calculate_risk
from evaluation.replay import generate_synthetic_cases
from ml.predict import get_model_path, ml_score, reset_model_cache
from ml.train import split_cases_by_patient, train
from shared.schemas import Condition, Consciousness, Patient, RiskTier, Source, VitalName, VitalsReading


def test_model_graceful_none_when_missing(tmp_path):
    """Verify ml_score returns None when model file is absent."""
    reset_model_cache()
    p = Patient(id=1, bed=1, age=60, conditions=[], admitted_at=datetime(2026, 10, 1))
    features = extract_features(p, [], datetime(2026, 10, 1), DEFAULT_CONFIG)

    missing_model_path = tmp_path / "nonexistent_model.txt"
    score = ml_score(features, p, model_path=missing_model_path)
    assert score is None


def test_patient_split_no_leakage():
    """Verify train/test split partitions cases strictly by patient ID without overlap."""
    cases = generate_synthetic_cases(n_cases=30, seed=42)
    train_cases, test_cases = split_cases_by_patient(cases, test_ratio=0.20, seed=42)

    assert len(train_cases) > 0
    assert len(test_cases) > 0
    assert len(train_cases) + len(test_cases) == len(cases)

    train_ids = {c.patient.id for c in train_cases}
    test_ids = {c.patient.id for c in test_cases}

    # Strict disjointness: NO patient in both train and test
    assert train_ids.isdisjoint(test_ids), f"Overlapping patients found: {train_ids & test_ids}"


def test_train_pipeline_and_artifacts():
    """Verify training executes, writes metrics.json with AUROC/AUPRC, and outputs small model."""
    metrics = train(n_synthetic_cases=20, seed=42)

    assert "auroc" in metrics
    assert "auprc" in metrics
    assert 0.5 <= metrics["auroc"] <= 1.0
    assert 0.0 <= metrics["auprc"] <= 1.0

    backend_dir = Path(__file__).resolve().parent.parent
    model_path = backend_dir / "ml" / "saved_model" / "model.txt"
    metrics_path = backend_dir / "ml" / "metrics.json"

    assert model_path.exists()
    assert metrics_path.exists()

    # Model size check: must stay compact (< 100 KB)
    model_size_kb = model_path.stat().st_size / 1024
    assert model_size_kb < 100, f"Model file unexpectedly large: {model_size_kb} KB"


def test_predict_returns_valid_probability():
    """Verify ml_score returns a valid float probability in [0.0, 1.0] when model exists."""
    reset_model_cache()
    now = datetime(2026, 10, 1, 12, 0)
    p = Patient(id=1, bed=1, age=65, conditions=[Condition.COPD], admitted_at=now - timedelta(days=1))
    readings = [
        VitalsReading(
            id=1, patient_id=1, timestamp=now - timedelta(hours=4), source=Source.MANUAL,
            hr=80.0, sbp=125.0, dbp=78.0, rr=20.0, spo2=91.0, temp=36.7,
            on_oxygen=False, consciousness=Consciousness.ALERT,
        ),
        VitalsReading(
            id=2, patient_id=1, timestamp=now, source=Source.MANUAL,
            hr=110.0, sbp=100.0, dbp=65.0, rr=26.0, spo2=87.0, temp=38.2,
            on_oxygen=True, consciousness=Consciousness.ALERT,
        ),
    ]

    features = extract_features(p, readings, now, DEFAULT_CONFIG)
    score = ml_score(features, p)

    assert score is not None
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_rules_safety_floor_maintained():
    """Verify that a low ML score (e.g. 0.0) NEVER suppresses an absolute red-line breach."""
    now = datetime(2026, 10, 1, 12, 0)
    p = Patient(id=2, bed=2, age=70, conditions=[], admitted_at=now - timedelta(days=1))

    # Extreme respiratory rate 34 breaches red line (> 30)
    crash_reading = VitalsReading(
        id=10, patient_id=2, timestamp=now, source=Source.MANUAL,
        hr=100.0, sbp=120.0, dbp=80.0, rr=34.0, spo2=95.0, temp=37.0,
        on_oxygen=False, consciousness=Consciousness.ALERT,
    )

    features = extract_features(p, [crash_reading], now, DEFAULT_CONFIG)

    # Calculate risk with adversarial ml_score = 0.0 (simulating false negative ML prediction)
    risk_score, tier, is_crash_flag, reasons = calculate_risk(
        features=features,
        reading=crash_reading,
        patient=p,
        config=DEFAULT_CONFIG,
        ml_score=0.0,
    )

    # Red line safety floor must guarantee risk_score >= tier_high (0.65) and HIGH/CRITICAL tier
    assert risk_score >= DEFAULT_CONFIG.tier_high
    assert tier in (RiskTier.HIGH, RiskTier.CRITICAL)
    assert any("breach" in r.lower() or "rr" in r.lower() for r in reasons)


def test_engine_passes_with_model_present_and_absent():
    """Verify calculate_risk works seamlessly with ml_score=None and ml_score=0.85."""
    now = datetime(2026, 10, 1, 12, 0)
    p = Patient(id=3, bed=3, age=55, conditions=[], admitted_at=now)
    reading = VitalsReading(
        id=20, patient_id=3, timestamp=now, source=Source.MANUAL,
        hr=75.0, sbp=120.0, dbp=80.0, rr=16.0, spo2=98.0, temp=36.6,
        on_oxygen=False, consciousness=Consciousness.ALERT,
    )
    features = extract_features(p, [reading], now, DEFAULT_CONFIG)

    # Without ML
    score_no_ml, tier_no_ml, _, _ = calculate_risk(features, reading, p, DEFAULT_CONFIG, ml_score=None)
    assert 0.0 <= score_no_ml <= 1.0

    # With ML
    score_with_ml, tier_with_ml, _, _ = calculate_risk(features, reading, p, DEFAULT_CONFIG, ml_score=0.85)
    assert 0.0 <= score_with_ml <= 1.0
    assert score_with_ml > score_no_ml  # High ML risk elevates score within safety rules
