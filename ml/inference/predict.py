"""
FraudShield — Inference Engine
SHAP via XGBoost predict_contributions for fast explanations.
All objects cached at module level — never per-request.
"""

import pickle
import time
from pathlib import Path
from typing import Optional

import numpy as np
from xgboost import XGBClassifier, DMatrix
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path("ml/model.pkl")

# --- Module-level cache (loaded once, reused forever) ---
_model: Optional[XGBClassifier] = None
_booster = None
_scaler: Optional[StandardScaler] = None
_metadata: dict = {}
_threshold: float = 0.5

FEATURE_NAMES = [f"V{i}" for i in range(1, 29)] + ["Amount"]


def _load_model() -> None:
    """Load model.pkl into module-level cache."""
    global _model, _booster, _scaler, _metadata, _threshold
    if _model is not None:
        return

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    _model = bundle["model"]
    _booster = _model.get_booster()
    _scaler = bundle["scaler"]
    _metadata = bundle.get("metadata", {})
    _threshold = _metadata.get("metrics", {}).get("threshold", 0.5)


def _build_features(features: list[float], amount: float) -> np.ndarray:
    """Build feature array: [V1..V28, Amount_scaled]."""
    amount_scaled = _scaler.transform(np.array([[amount]]))[0, 0]
    return np.array([list(features) + [amount_scaled]], dtype=np.float32)


def predict(features: list[float], amount: float) -> dict:
    """
    Predict fraud probability with SHAP explanation.
    """
    _load_model()
    start = time.perf_counter()

    feature_array = _build_features(features, amount)
    prob = float(_model.predict_proba(feature_array)[0, 1])
    is_fraud = prob >= _threshold

    # SHAP explanation
    dm = DMatrix(feature_array)
    contributions = _booster.predict(dm, pred_contribs=True)[0]
    shap_vals = contributions[:-1]

    indices = np.argsort(np.abs(shap_vals))[::-1][:5]
    top_features = [
        {"feature": FEATURE_NAMES[i], "shap_value": round(float(shap_vals[i]), 6)}
        for i in indices
    ]

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "fraud_probability": round(prob, 6),
        "is_fraud": bool(is_fraud),
        "top_features": top_features,
        "latency_ms": round(elapsed_ms, 2),
    }


def predict_fast(features: list[float], amount: float) -> dict:
    """Fast prediction without SHAP (for batch/high-throughput)."""
    _load_model()
    start = time.perf_counter()

    feature_array = _build_features(features, amount)
    prob = float(_model.predict_proba(feature_array)[0, 1])

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "fraud_probability": round(prob, 6),
        "is_fraud": bool(prob >= _threshold),
        "latency_ms": round(elapsed_ms, 2),
    }


def explain(features: list[float], amount: float) -> dict:
    """Compute SHAP explanation for a transaction (called on demand)."""
    _load_model()
    start = time.perf_counter()

    feature_array = _build_features(features, amount)
    dm = DMatrix(feature_array)
    contributions = _booster.predict(dm, pred_contribs=True)[0]
    shap_vals = contributions[:-1]
    base_value = float(contributions[-1])  # bias/expected value

    indices = np.argsort(np.abs(shap_vals))[::-1][:5]
    top_features = [
        {"feature": FEATURE_NAMES[i], "shap_value": round(float(shap_vals[i]), 6)}
        for i in indices
    ]

    # Convert base value from log-odds to probability space
    base_prob = float(1 / (1 + np.exp(-base_value)))

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "base_value": round(base_value, 6),
        "base_probability": round(base_prob, 6),
        "top_features": top_features,
        "latency_ms": round(elapsed_ms, 2),
    }


def predict_batch(transactions: list[dict]) -> list[dict]:
    """Batch prediction for multiple transactions."""
    return [predict(t["features"], t["amount"]) for t in transactions]


def get_model_metadata() -> dict:
    """Return model metadata (NOT the model itself)."""
    _load_model()
    return _metadata
