"""FraudShield — Pydantic schemas for all API inputs/outputs."""

from typing import Optional
from pydantic import BaseModel, Field


# --- Request schemas ---

class PredictRequest(BaseModel):
    """Single transaction prediction request."""
    amount: float = Field(..., ge=0, description="Transaction amount")
    features: list[float] = Field(
        ..., min_length=28, max_length=28,
        description="V1-V28 feature values (28 floats)"
    )


class BatchRequest(BaseModel):
    """Batch prediction request."""
    transactions: list[PredictRequest] = Field(
        ..., min_length=1, max_length=100,
        description="1-100 transactions to score"
    )


# --- Response schemas ---

class SHAPFeature(BaseModel):
    feature: str
    shap_value: float


class PredictResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    top_features: list[SHAPFeature]
    latency_ms: float
    transaction_id: Optional[int] = None


class BatchResponse(BaseModel):
    results: list[PredictResponse]
    total_latency_ms: float


class TransactionRecord(BaseModel):
    id: int
    amount: float
    fraud_probability: float
    is_fraud: bool
    top_features: list[SHAPFeature]
    latency_ms: float
    created_at: str


class StatsResponse(BaseModel):
    total_transactions: int
    total_fraud: int
    fraud_rate: float
    avg_latency_ms: float
    model_f1: float
    model_auc_roc: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ExplainResponse(BaseModel):
    transaction_id: int
    fraud_probability: float
    is_fraud: bool
    top_features: list[SHAPFeature]
    latency_ms: float
