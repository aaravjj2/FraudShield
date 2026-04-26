"""FraudShield — API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from api.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True


def test_predict_fraud():
    """Test with real fraud features from dataset (should detect fraud)."""
    r = client.post("/predict", json={
        "amount": 0.0,
        "features": [-2.31, 1.95, -1.61, 4.0, -0.52, -1.43, -2.54, 1.39,
                      -2.77, -2.77, 3.2, -2.9, -0.6, -4.29, 0.39, -1.14,
                      -2.83, -0.02, 0.42, 0.13, 0.52, -0.04, -0.47, 0.32,
                      0.04, 0.18, 0.26, -0.14]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["is_fraud"] is True
    assert data["fraud_probability"] > 0.5
    assert data["transaction_id"] is not None

    # SHAP via explain endpoint
    tx_id = data["transaction_id"]
    r2 = client.get(f"/explain/{tx_id}")
    assert r2.status_code == 200
    explanation = r2.json()
    assert explanation["transaction_id"] == tx_id
    assert len(explanation["top_features"]) == 5


def test_predict_legit():
    """Test with normal transaction (should be legit)."""
    r = client.post("/predict", json={
        "amount": 42.50,
        "features": [0.1, 0.2, 0.1, -0.1, 0.05, -0.02, 0.01, -0.03,
                      0.02, 0.01, -0.01, 0.03, -0.02, 0.01, 0.0, -0.01,
                      0.02, 0.0, 0.01, -0.01, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0, 0.0]
    })
    assert r.status_code == 200
    data = r.json()
    assert "fraud_probability" in data
    assert "top_features" in data


def test_predict_validation():
    """Test input validation — wrong number of features."""
    r = client.post("/predict", json={"amount": 100, "features": [1.0, 2.0]})
    assert r.status_code == 422


def test_batch():
    """Test batch prediction."""
    r = client.post("/batch", json={
        "transactions": [
            {"amount": 100, "features": [0.0]*28},
            {"amount": 500, "features": [0.0]*28},
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 2
    assert data["total_latency_ms"] > 0


def test_transactions():
    """Test transaction listing."""
    # First create one
    client.post("/predict", json={"amount": 100, "features": [0.0]*28})

    r = client.get("/transactions")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "amount" in data[0]
    assert "is_fraud" in data[0]


def test_stats():
    """Test stats endpoint."""
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_transactions"] >= 0
    assert data["model_f1"] > 0.8
    assert data["model_auc_roc"] > 0.9
