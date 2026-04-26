"""
FraudShield — FastAPI Application
Real-Time AI Fraud Detection API

Endpoints: POST /predict, POST /batch, GET /transactions, GET /stats, GET /health
Swagger: /docs
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.schemas import (
    PredictRequest, PredictResponse, BatchRequest, BatchResponse,
    TransactionRecord, StatsResponse, HealthResponse, SHAPFeature,
)
from api.database import init_db, insert_transaction, get_transactions, get_stats

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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — is the model loaded?"""
    try:
        from ml.inference.predict import get_model_metadata
        meta = get_model_metadata()
        return HealthResponse(status="ok", model_loaded=True)
    except Exception:
        return HealthResponse(status="ok", model_loaded=False)


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """Score a single transaction for fraud probability with SHAP explanation."""
    from ml.inference.predict import predict as ml_predict

    result = ml_predict(req.features, req.amount)

    tx_id = insert_transaction(
        amount=req.amount,
        fraud_probability=result["fraud_probability"],
        is_fraud=result["is_fraud"],
        top_features=result["top_features"],
        latency_ms=result["latency_ms"],
    )

    return PredictResponse(
        fraud_probability=result["fraud_probability"],
        is_fraud=result["is_fraud"],
        top_features=[SHAPFeature(**f) for f in result["top_features"]],
        latency_ms=result["latency_ms"],
        transaction_id=tx_id,
    )


@app.post("/batch", response_model=BatchResponse)
async def batch_predict(req: BatchRequest):
    """Score multiple transactions (1-100) for fraud."""
    import time
    from ml.inference.predict import predict as ml_predict

    start = time.perf_counter()
    results = []
    for tx in req.transactions:
        result = ml_predict(tx.features, tx.amount)
        tx_id = insert_transaction(
            amount=tx.amount,
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            top_features=result["top_features"],
            latency_ms=result["latency_ms"],
        )
        results.append(PredictResponse(
            fraud_probability=result["fraud_probability"],
            is_fraud=result["is_fraud"],
            top_features=[SHAPFeature(**f) for f in result["top_features"]],
            latency_ms=result["latency_ms"],
            transaction_id=tx_id,
        ))
    total_ms = (time.perf_counter() - start) * 1000

    return BatchResponse(results=results, total_latency_ms=round(total_ms, 2))


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
    import json
    items = json.loads(features_json)
    return [SHAPFeature(**f) for f in items]
