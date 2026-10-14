"""
WardPulse LightGBM Inference Service (P8).

Loads the trained model from backend/ml/saved_model/model.txt if present,
and provides ml_score(features) -> float | None.
Returns None gracefully if no model file exists or if an error occurs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np

from engine.features import PatientFeatures
from ml.features import extract_feature_vector
from shared.schemas import Patient


_CACHED_MODEL: Optional[lgb.Booster] = None
_CACHED_MODEL_PATH: Optional[Path] = None


def get_model_path() -> Path:
    """Return default path to saved model file."""
    return Path(__file__).resolve().parent / "saved_model" / "model.txt"


def reset_model_cache() -> None:
    """Clear in-memory cached model (useful for unit tests)."""
    global _CACHED_MODEL, _CACHED_MODEL_PATH
    _CACHED_MODEL = None
    _CACHED_MODEL_PATH = None


def load_model(model_path: Optional[Path] = None) -> Optional[lgb.Booster]:
    """Load and cache LightGBM booster from disk, or return None if not present."""
    global _CACHED_MODEL, _CACHED_MODEL_PATH

    path = model_path or get_model_path()

    if _CACHED_MODEL is not None and _CACHED_MODEL_PATH == path:
        return _CACHED_MODEL

    if not path.exists():
        return None

    try:
        booster = lgb.Booster(model_file=str(path))
        _CACHED_MODEL = booster
        _CACHED_MODEL_PATH = path
        return _CACHED_MODEL
    except Exception as e:
        print(f"Warning: Failed to load LightGBM model from {path}: {e}")
        return None


def ml_score(
    features: PatientFeatures,
    patient: Optional[Patient] = None,
    model_path: Optional[Path] = None,
) -> Optional[float]:
    """Predict acute deterioration probability in [0.0, 1.0] from patient features.
    
    Returns None if no model file exists, allowing the rule-based engine to operate
    unimpeded without ML.
    """
    model = load_model(model_path)
    if model is None:
        return None

    try:
        vector = extract_feature_vector(features, patient)
        arr = np.array([vector], dtype=np.float32)
        prediction = model.predict(arr)[0]
        # Return probability clamped to [0.0, 1.0]
        prob = float(prediction)
        return max(0.0, min(1.0, round(prob, 4)))
    except Exception as e:
        print(f"Warning: ml_score inference error: {e}")
        return None
