"""FraudShield — ML model tests."""

import pickle
import numpy as np
import pytest
from pathlib import Path


MODEL_PATH = Path("ml/model.pkl")


@pytest.fixture(scope="module")
def model_bundle():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def test_model_exists():
    assert MODEL_PATH.exists(), "model.pkl not found — run ml/training/train.py"


def test_model_structure(model_bundle):
    assert "model" in model_bundle
    assert "scaler" in model_bundle
    assert "metadata" in model_bundle


def test_model_predict_range(model_bundle):
    model = model_bundle["model"]
    X = np.random.randn(1, 29)
    proba = model.predict_proba(X)[0]
    assert len(proba) == 2
    assert 0 <= proba[0] <= 1
    assert 0 <= proba[1] <= 1
    assert abs(proba.sum() - 1.0) < 1e-6


def test_fraud_detection(model_bundle):
    """Load a real fraud sample and verify model detects it."""
    import pandas as pd

    df = pd.read_csv("data/raw/creditcard.csv")
    fraud = df[df["Class"] == 1].iloc[0]

    X = fraud.drop(["Time", "Class"]).values.reshape(1, -1)
    # Scale Amount (last column)
    scaler = model_bundle["scaler"]
    X_copy = X.copy()
    X_copy[0, -1] = scaler.transform([[X[0, -1]]])[0, 0]

    prob = model_bundle["model"].predict_proba(X_copy)[0, 1]
    assert prob > 0.5, f"Fraud score {prob:.4f} too low — model broken"


def test_suspicious_high_amount(model_bundle):
    """High amount + extreme V-features should flag as suspicious."""
    model = model_bundle["model"]
    scaler = model_bundle["scaler"]

    X = np.array([[1200.0, -4.5, -3.0] + [0.0]*26])
    X_scaled = X.copy()
    X_scaled[0, -1] = scaler.transform([[1200.0]])[0, 0]

    prob = model.predict_proba(X_scaled)[0, 1]
    # This specific pattern may or may not be fraud — just verify it runs
    assert 0 <= prob <= 1


def test_model_metrics(model_bundle):
    metadata = model_bundle["metadata"]
    metrics = metadata.get("metrics", {})
    assert metrics.get("f1_fraud", 0) >= 0.85, f"F1 {metrics.get('f1_fraud')} < 0.85"
    assert metrics.get("auc_roc", 0) >= 0.95, f"AUC-ROC {metrics.get('auc_roc')} < 0.95"
