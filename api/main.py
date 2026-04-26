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
    ExplainResponse, ModelInfoResponse,
)
from api.database import init_db, insert_transaction, get_transactions, get_transaction, get_stats
from api.middleware import TimingMiddleware

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

app.add_middleware(TimingMiddleware)

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

    result = ml_explain(features, tx["amount"])

    return ExplainResponse(
        transaction_id=tx_id,
        fraud_probability=tx["fraud_probability"],
        is_fraud=bool(tx["is_fraud"]),
        base_value=result["base_value"],
        base_probability=result["base_probability"],
        top_features=[SHAPFeature(**f) for f in result["top_features"]],
        latency_ms=result["latency_ms"],
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


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info():
    """Get detailed model information and hyperparameters."""
    from ml.inference.predict import get_model_metadata
    meta = get_model_metadata()
    metrics = meta.get("metrics", {})

    return ModelInfoResponse(
        model_type="XGBoost",
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=577.3,
        decision_threshold=metrics.get("threshold", 0.5),
        f1_fraud=metrics.get("f1_fraud", 0.0),
        auc_roc=metrics.get("auc_roc", 0.0),
        training_samples=227845,
        n_features=29,
        trained_at=meta.get("trained_at", "unknown"),
    )


@app.post("/simulate", response_model=list[PredictResponse])
async def simulate(
    count: int = Query(default=10, ge=1, le=50, description="Number of transactions"),
):
    """Generate simulated transactions for live demo. Guarantees 2 fraud."""
    import numpy as np
    from ml.inference.predict import predict_fast

    rng = np.random.default_rng()
    results = []

    # Guarantee at least 2 fraud transactions (from real fraud samples)
    fraud_count = min(2, count)
    legit_count = count - fraud_count

    fraud_samples = [
        {"amount": 0.0, "features": [-2.31, 1.95, -1.61, 4.0, -0.52, -1.43, -2.54, 1.39, -2.77, -2.77, 3.2, -2.9, -0.6, -4.29, 0.39, -1.14, -2.83, -0.02, 0.42, 0.13, 0.52, -0.04, -0.47, 0.32, 0.04, 0.18, 0.26, -0.14]},
        {"amount": 239.93, "features": [-2.26, -3.81, 2.99, 2.95, -0.21, 2.47, -1.47, 1.21, -1.22, -0.62, -0.48, -0.91, -0.53, 0.47, 0.71, 0.30, 0.68, 0.04, -0.13, -0.11, -0.15, 0.19, -0.07, 0.11, -0.05, 0.01, -0.01, 0.03]},
    ]

    for i in range(fraud_count):
        sample = fraud_samples[i % len(fraud_samples)]
        noisy_features = [f + rng.normal(0, 0.1) for f in sample["features"]]
        result = predict_fast(noisy_features, sample["amount"])
        tx_id = insert_transaction(
            amount=round(sample["amount"], 2),
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            latency_ms=result["latency_ms"],
            features=noisy_features,
        )
        results.append(PredictResponse(
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            top_features=[],
            latency_ms=result["latency_ms"],
            transaction_id=tx_id,
        ))

    for _ in range(legit_count):
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

    # Shuffle so fraud isn't always first
    rng.shuffle(np.array(results))
    return results
