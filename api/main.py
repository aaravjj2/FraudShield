"""
FraudShield — FastAPI Application
Real-Time AI Fraud Detection API

Endpoints: POST /predict, POST /batch, GET /transactions, GET /stats, GET /health, GET /explain/{id}
Swagger: /docs
"""

import json
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.schemas import (
    PredictRequest, PredictResponse, BatchRequest, BatchResponse,
    TransactionRecord, StatsResponse, HealthResponse, SHAPFeature,
    ExplainResponse,
)
from api.database import init_db, insert_transaction, get_transactions, get_transaction, get_stats

# Lifespan: init DB on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="FraudShield",
    description="Real-Time AI Fraud Detection API — XGBoost + SHAP Explainability",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — is the model loaded?"""
    try:
        from ml.inference.predict import get_model_metadata
        get_model_metadata()
        return HealthResponse(status="ok", model_loaded=True)
    except Exception:
        return HealthResponse(status="ok", model_loaded=False)


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """Score a single transaction — FAST (no SHAP). Use /explain/{id} for SHAP."""
    from ml.inference.predict import predict_fast

    result = predict_fast(req.features, req.amount)

    tx_id = insert_transaction(
        amount=req.amount,
        fraud_probability=result["fraud_probability"],
        is_fraud=result["is_fraud"],
        latency_ms=result["latency_ms"],
        features=req.features,
    )

    return PredictResponse(
        fraud_probability=result["fraud_probability"],
        is_fraud=result["is_fraud"],
        top_features=[],
        latency_ms=result["latency_ms"],
        transaction_id=tx_id,
    )


@app.post("/batch", response_model=BatchResponse)
async def batch_predict(req: BatchRequest):
    """Score multiple transactions (1-100) for fraud."""
    from ml.inference.predict import predict_fast

    start = time.perf_counter()
    results = []
    for tx in req.transactions:
        result = predict_fast(tx.features, tx.amount)
        tx_id = insert_transaction(
            amount=tx.amount,
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            latency_ms=result["latency_ms"],
            features=tx.features,
        )
        results.append(PredictResponse(
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            top_features=[],
            latency_ms=result["latency_ms"],
            transaction_id=tx_id,
        ))
    total_ms = (time.perf_counter() - start) * 1000

    return BatchResponse(results=results, total_latency_ms=round(total_ms, 2))


@app.get("/explain/{tx_id}", response_model=ExplainResponse)
async def explain(tx_id: int):
    """Get SHAP explanation for a stored transaction."""
    from ml.inference.predict import explain as ml_explain

    tx = get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    features = json.loads(tx["features"])
    if len(features) != 28:
        raise HTTPException(status_code=400, detail="Transaction has no stored features")

    start = time.perf_counter()
    top_features = ml_explain(features, tx["amount"])
    shap_ms = (time.perf_counter() - start) * 1000

    return ExplainResponse(
        transaction_id=tx_id,
        fraud_probability=tx["fraud_probability"],
        is_fraud=bool(tx["is_fraud"]),
        top_features=[SHAPFeature(**f) for f in top_features],
        latency_ms=round(shap_ms, 2),
    )


@app.get("/transactions", response_model=list[TransactionRecord])
async def transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Get recent transactions."""
    rows = get_transactions(limit=limit, offset=offset)
    return [
        TransactionRecord(
            id=r["id"],
            amount=r["amount"],
            fraud_probability=r["fraud_probability"],
            is_fraud=bool(r["is_fraud"]),
            top_features=json_to_shap(r["top_features"]),
            latency_ms=r["latency_ms"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.get("/stats", response_model=StatsResponse)
async def stats():
    """Get fraud detection statistics."""
    from ml.inference.predict import get_model_metadata

    db_stats = get_stats()
    meta = get_model_metadata()
    metrics = meta.get("metrics", {})

    return StatsResponse(
        total_transactions=db_stats["total_transactions"],
        total_fraud=db_stats["total_fraud"],
        fraud_rate=db_stats["fraud_rate"],
        avg_latency_ms=db_stats["avg_latency_ms"],
        model_f1=metrics.get("f1_fraud", 0.0),
        model_auc_roc=metrics.get("auc_roc", 0.0),
    )


def json_to_shap(features_json: str) -> list[SHAPFeature]:
    """Parse stored JSON features into SHAPFeature list."""
    items = json.loads(features_json)
    return [SHAPFeature(**f) for f in items]


@app.post("/simulate", response_model=list[PredictResponse])
async def simulate(
    count: int = Query(default=10, ge=1, le=50, description="Number of transactions"),
):
    """Generate simulated transactions for live demo. Mix of fraud + legit."""
    import numpy as np
    from ml.inference.predict import predict_fast

    rng = np.random.default_rng()
    results = []

    for _ in range(count):
        # 20% chance of fraud-like features using real fraud patterns
        is_fraud_sim = rng.random() < 0.20

        if is_fraud_sim:
            # Based on real fraud patterns from the dataset
            features = rng.normal(0, 1.5, 28).tolist()
            features[0] = rng.uniform(-4, -1)   # V1
            features[3] = rng.uniform(2, 6)     # V4 — strong fraud indicator
            features[9] = rng.uniform(-5, -2)   # V10
            features[11] = rng.uniform(-4, -1)  # V12
            features[13] = rng.uniform(-6, -3)  # V14 — strongest fraud indicator
            amount = rng.uniform(50, 3000)
        else:
            # Normal: centered features, typical amounts
            features = rng.normal(0, 1, 28).tolist()
            amount = rng.uniform(1, 500)

        result = predict_fast(features, amount)
        tx_id = insert_transaction(
            amount=round(amount, 2),
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            latency_ms=result["latency_ms"],
            features=features,
        )
        results.append(PredictResponse(
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            top_features=[],
            latency_ms=result["latency_ms"],
            transaction_id=tx_id,
        ))

    return results
