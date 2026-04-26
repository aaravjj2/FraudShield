"""FraudShield — Latency benchmark tests.

Run with: pytest tests/test_latency.py -v -s
Note: When run with other tests, WSL2 overhead + rate limiter may affect timings.
"""

import time
import statistics
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


class TestLatencyBenchmark:
    """Benchmark critical API endpoints.
    In WSL2, expect 10-100x overhead vs native Linux.
    Targets: /predict <10ms, /explain <50ms on native."""

    def test_predict_latency_single(self):
        """Single prediction latency benchmark (20 iterations)."""
        latencies = []
        payload = {"amount": 100.0, "features": [0.0] * 28}
        # Warm up
        client.post("/predict", json=payload)

        for _ in range(20):
            start = time.perf_counter()
            r = client.post("/predict", json=payload)
            elapsed = (time.perf_counter() - start) * 1000
            assert r.status_code == 200
            latencies.append(elapsed)

        avg = statistics.mean(latencies)
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        print(f"\n/predict latency: avg={avg:.2f}ms, p50={p50:.2f}ms, p95={p95:.2f}ms")
        assert avg < 500, f"Average latency {avg:.2f}ms too high"

    def test_batch_latency(self):
        """Batch prediction latency benchmark."""
        payload = {
            "transactions": [
                {"amount": float(i), "features": [0.0] * 28} for i in range(10)
            ]
        }
        start = time.perf_counter()
        r = client.post("/batch", json=payload)
        elapsed = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        per_tx = elapsed / 10
        print(f"\n/batch(10) latency: total={elapsed:.2f}ms, per_tx={per_tx:.2f}ms")
        assert per_tx < 500

    def test_explain_latency(self):
        """SHAP explanation latency benchmark."""
        r = client.post("/predict", json={"amount": 100, "features": [0.0] * 28})
        tx_id = r.json()["transaction_id"]

        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            r2 = client.get(f"/explain/{tx_id}")
            elapsed = (time.perf_counter() - start) * 1000
            assert r2.status_code == 200
            latencies.append(elapsed)

        avg = statistics.mean(latencies)
        print(f"\n/explain latency: avg={avg:.2f}ms")

    def test_health_latency(self):
        """Health check latency."""
        start = time.perf_counter()
        r = client.get("/health")
        elapsed = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        print(f"\n/health latency: {elapsed:.2f}ms")

    def test_stats_latency(self):
        """Stats endpoint latency."""
        start = time.perf_counter()
        r = client.get("/stats")
        elapsed = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        print(f"\n/stats latency: {elapsed:.2f}ms")
