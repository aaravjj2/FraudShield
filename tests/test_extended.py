"""FraudShield — Extended API tests for simulate, explain, and edge cases."""

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


class TestSimulateEndpoint:
    def test_simulate_default(self):
        r = client.post("/simulate")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 10

    def test_simulate_custom_count(self):
        r = client.post("/simulate?count=5")
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_simulate_guarantees_fraud(self):
        """Simulate should always produce at least 1 fraud."""
        r = client.post("/simulate?count=10")
        data = r.json()
        frauds = [tx for tx in data if tx["is_fraud"]]
        assert len(frauds) >= 1

    def test_simulate_has_transaction_ids(self):
        r = client.post("/simulate?count=3")
        for tx in r.json():
            assert tx["transaction_id"] is not None
            assert tx["fraud_probability"] >= 0

    def test_simulate_count_limit(self):
        r = client.post("/simulate?count=0")
        assert r.status_code == 422  # ge=1

    def test_simulate_count_max(self):
        r = client.post("/simulate?count=51")
        assert r.status_code == 422  # le=50


class TestExplainEndpoint:
    def test_explain_existing_transaction(self):
        # Create a transaction first
        r = client.post("/predict", json={
            "amount": 100, "features": [0.0]*28
        })
        tx_id = r.json()["transaction_id"]

        r2 = client.get(f"/explain/{tx_id}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["transaction_id"] == tx_id
        assert len(data["top_features"]) == 5
        assert "base_value" in data
        assert "base_probability" in data

    def test_explain_nonexistent(self):
        r = client.get("/explain/99999")
        assert r.status_code == 404


class TestEdgeCases:
    def test_predict_zero_amount(self):
        r = client.post("/predict", json={"amount": 0, "features": [0.0]*28})
        assert r.status_code == 200

    def test_predict_large_amount(self):
        r = client.post("/predict", json={"amount": 999999.99, "features": [0.0]*28})
        assert r.status_code == 200

    def test_predict_extreme_features(self):
        r = client.post("/predict", json={
            "amount": 100,
            "features": [10.0]*28
        })
        assert r.status_code == 200
        assert 0 <= r.json()["fraud_probability"] <= 1

    def test_batch_single(self):
        r = client.post("/batch", json={
            "transactions": [{"amount": 100, "features": [0.0]*28}]
        })
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

    def test_transactions_pagination(self):
        # Create some transactions
        for _ in range(5):
            client.post("/predict", json={"amount": 100, "features": [0.0]*28})

        r1 = client.get("/transactions?limit=2&offset=0")
        assert len(r1.json()) == 2

        r2 = client.get("/transactions?limit=2&offset=2")
        assert len(r2.json()) == 2

    def test_stats_after_transactions(self):
        client.post("/simulate?count=10")
        r = client.get("/stats")
        data = r.json()
        assert data["total_transactions"] >= 10
        assert data["model_f1"] > 0.85
        assert data["model_auc_roc"] > 0.95
