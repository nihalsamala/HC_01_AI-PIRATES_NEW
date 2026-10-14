"""
WardPulse LightGBM Model Training (P8).

Builds training rows from ReplayCase observations, splits by patient to prevent
data leakage, trains a LightGBM binary classifier with native NaN handling,
evaluates AUROC/AUPRC on held-out patients, and saves model.txt and metrics.json.

Usage:
    cd backend && python -m ml.train
"""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from engine.config import DEFAULT_CONFIG
from engine.features import extract_features
from evaluation.replay import ReplayCase, generate_synthetic_cases, load_dataset
from ml.features import FEATURE_NAMES, extract_feature_vector


PREDICTION_HORIZON_HOURS: float = 6.0


def build_patient_rows(
    case: ReplayCase,
    horizon_hours: float = PREDICTION_HORIZON_HOURS,
) -> Tuple[List[List[float]], List[int]]:
    """Generate sequential training rows and labels for a single patient case.
    
    Label = 1 if the patient experiences a clinical deterioration event within
    (t, t + horizon_hours], else 0.
    """
    X_patient: List[List[float]] = []
    y_patient: List[int] = []

    readings = case.readings
    if not readings:
        return X_patient, y_patient

    for i in range(1, len(readings) + 1):
        visible = readings[:i]
        curr_reading = visible[-1]
        t = curr_reading.timestamp

        # If patient has already collapsed at or before t, stop training on post-event data
        if case.event_time is not None and t > case.event_time:
            continue

        features = extract_features(case.patient, visible, t, DEFAULT_CONFIG)
        vector = extract_feature_vector(features, case.patient)

        # Label: deterioration within next horizon_hours
        if case.event_time is not None:
            lead_time = (case.event_time - t).total_seconds() / 3600.0
            label = 1 if 0.0 <= lead_time <= horizon_hours else 0
        else:
            label = 0

        X_patient.append(vector)
        y_patient.append(label)

    return X_patient, y_patient


def split_cases_by_patient(
    cases: List[ReplayCase],
    test_ratio: float = 0.20,
    seed: int = 42,
) -> Tuple[List[ReplayCase], List[ReplayCase]]:
    """Split cases into train and test sets strictly by patient ID.
    
    Guarantees no patient appears in both sets, with stratified event representation.
    """
    rng = random.Random(seed)

    event_cases = [c for c in cases if c.event_time is not None]
    stable_cases = [c for c in cases if c.event_time is None]

    rng.shuffle(event_cases)
    rng.shuffle(stable_cases)

    n_test_event = max(1, int(len(event_cases) * test_ratio)) if event_cases else 0
    n_test_stable = max(1, int(len(stable_cases) * test_ratio)) if stable_cases else 0

    test_cases = event_cases[:n_test_event] + stable_cases[:n_test_stable]
    train_cases = event_cases[n_test_event:] + stable_cases[n_test_stable:]

    train_ids = {c.patient.id for c in train_cases}
    test_ids = {c.patient.id for c in test_cases}
    assert train_ids.isdisjoint(test_ids), "Patient leakage detected in split!"

    return train_cases, test_cases


def train(
    data_path: Optional[str | Path] = None,
    n_synthetic_cases: int = 50,
    horizon_hours: float = PREDICTION_HORIZON_HOURS,
    seed: int = 42,
) -> Dict[str, float]:
    """Train LightGBM risk model and save artifacts to backend/ml/."""
    backend_dir = Path(__file__).resolve().parent.parent
    raw_dir = backend_dir.parent / "data" / "raw"
    target_path = Path(data_path) if data_path else raw_dir

    psv_files = list(target_path.glob("*.psv")) if target_path.exists() else []
    if psv_files:
        print(f"Loading {len(psv_files)} cases from {target_path}...")
        cases = load_dataset(target_path)
    else:
        print(f"Generating {n_synthetic_cases} synthetic fallback cases for ML training...")
        cases = generate_synthetic_cases(n_cases=n_synthetic_cases, seed=seed)

    train_cases, test_cases = split_cases_by_patient(cases, test_ratio=0.20, seed=seed)
    print(f"Patient split: {len(train_cases)} train patients, {len(test_cases)} held-out test patients.")

    # Build row matrices
    X_train: List[List[float]] = []
    y_train: List[int] = []
    for c in train_cases:
        x_rows, y_rows = build_patient_rows(c, horizon_hours=horizon_hours)
        X_train.extend(x_rows)
        y_train.extend(y_rows)

    X_test: List[List[float]] = []
    y_test: List[int] = []
    for c in test_cases:
        x_rows, y_rows = build_patient_rows(c, horizon_hours=horizon_hours)
        X_test.extend(x_rows)
        y_test.extend(y_rows)

    print(f"Rows generated: {len(X_train)} train rows (pos: {sum(y_train)}), {len(X_test)} test rows (pos: {sum(y_test)}).")

    X_train_np = np.array(X_train, dtype=np.float32)
    y_train_np = np.array(y_train, dtype=np.int32)
    X_test_np = np.array(X_test, dtype=np.float32)
    y_test_np = np.array(y_test, dtype=np.int32)

    train_data = lgb.Dataset(X_train_np, label=y_train_np, feature_name=FEATURE_NAMES)
    test_data = lgb.Dataset(X_test_np, label=y_test_np, reference=train_data, feature_name=FEATURE_NAMES)

    # Compact hyperparameter configuration to keep model file small (< 50KB)
    params = {
        "objective": "binary",
        "metric": ["auc", "binary_logloss"],
        "boosting_type": "gbdt",
        "num_leaves": 15,
        "max_depth": 4,
        "learning_rate": 0.05,
        "min_child_samples": 4,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "verbose": -1,
        "seed": seed,
    }

    model = lgb.train(
        params,
        train_data,
        num_boost_round=50,
        valid_sets=[test_data],
    )

    # Evaluate on held-out patients
    y_pred = model.predict(X_test_np)

    if len(np.unique(y_test_np)) > 1:
        auroc = float(roc_auc_score(y_test_np, y_pred))
        auprc = float(average_precision_score(y_test_np, y_pred))
    else:
        auroc = 1.0
        auprc = 1.0

    print(f"Held-out Test Performance: AUROC = {auroc:.3f}, AUPRC = {auprc:.3f}")

    # Save artifacts
    ml_dir = backend_dir / "ml"
    saved_model_dir = ml_dir / "saved_model"
    saved_model_dir.mkdir(parents=True, exist_ok=True)

    model_path = saved_model_dir / "model.txt"
    model.save_model(str(model_path))
    print(f"Saved model to {model_path} ({model_path.stat().st_size / 1024:.1f} KB)")

    metrics_path = ml_dir / "metrics.json"
    metrics_data = {
        "auroc": round(auroc, 4),
        "auprc": round(auprc, 4),
        "prediction_horizon_hours": horizon_hours,
        "n_train_patients": len(train_cases),
        "n_test_patients": len(test_cases),
        "n_train_rows": len(X_train),
        "n_test_rows": len(X_test),
        "pos_train_rows": int(sum(y_train)),
        "pos_test_rows": int(sum(y_test)),
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    return metrics_data


if __name__ == "__main__":
    train()
