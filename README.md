# FraudShield

> Real-Time AI Fraud Detection with SHAP Explainability

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2-orange)](https://xgboost.readthedocs.io)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![Tests](https://img.shields.io/badge/Tests-35%2F35-brightgreen)]()
[![F1](https://img.shields.io/badge/F1-0.8526-brightgreen)]()
[![AUC--ROC](https://img.shields.io/badge/AUC--ROC-0.9772-brightgreen)]()

**FraudShield** is a production-grade fraud detection platform built for financial institutions. It uses XGBoost with SHAP explainability to detect fraudulent transactions in real-time, with a live monitoring dashboard for operations teams.

Built for 5 concurrent hackathons with judging panels from **Goldman Sachs**, **Citibank**, and **ByteDance**.

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   React      │────▶│   FastAPI         │────▶│   XGBoost   │
│   Dashboard  │◀────│   + SQLite        │◀────│   + SHAP    │
│   (Vite)     │     │   + Pydantic      │     │   Model     │
└─────────────┘     └──────────────────┘     └─────────────┘
   :5173                :8000                   model.pkl
```

**3-tier architecture:**
- **ML Layer**: XGBoost classifier (200 trees, depth 5) with SHAP TreeExplainer
- **API Layer**: FastAPI with Pydantic validation, SQLite storage, async SHAP
- **Frontend**: React + TypeScript dashboard with live 2s polling

---

## Quick Start

```bash
# Docker Compose (recommended)
docker compose up --build

# Or run separately:
pip install -r requirements.txt
python ml/training/train.py          # Train model → ml/model.pkl
uvicorn api.main:app --port 8000     # Start API
cd dashboard && npm ci && npm run dev # Start dashboard
```

Open http://localhost:5173 for the dashboard, http://localhost:8000/docs for Swagger.

---

## API Endpoints

| Method | Endpoint | Description | Latency |
|--------|----------|-------------|---------|
| `POST` | `/predict` | Score a transaction | ~30ms* |
| `POST` | `/batch` | Score 1-100 transactions | ~26ms/tx |
| `GET` | `/explain/{id}` | SHAP explanation for a transaction | ~14ms |
| `GET` | `/transactions` | Recent transactions | < 5ms |
| `GET` | `/stats` | Detection statistics | < 5ms |
| `GET` | `/health` | Health check | < 3ms |
| `POST` | `/simulate` | Generate demo transactions (guarantees fraud) | ~300ms |
| `GET` | `/model-info` | Model hyperparameters and metrics | < 5ms |
| `GET` | `/export` | Export transactions as CSV | < 10ms |
| `GET` | `/metrics` | Prometheus-compatible monitoring | < 5ms |

\* WSL2 benchmarks: avg=30ms, p50=28ms. Model inference only: 0.03ms. Native Linux <10ms.

### Example: Detect Fraud

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 239.93,
    "features": [-2.31, 1.95, -1.61, 4.0, -0.52, -1.43, -2.54, 1.39,
                 -2.77, -2.77, 3.2, -2.9, -0.6, -4.29, 0.39, -1.14,
                 -2.83, -0.02, 0.42, 0.13, 0.52, -0.04, -0.47, 0.32,
                 0.04, 0.18, 0.26, -0.14]
  }'
```

Response:
```json
{
  "fraud_probability": 0.999957,
  "is_fraud": true,
  "latency_ms": 2.31,
  "transaction_id": 42
}
```

### Example: Get SHAP Explanation

```bash
curl http://localhost:8000/explain/42
```

Returns top 5 contributing features with SHAP values — compliant with **EU AI Act Art.13** and **SR 11-7** model validation requirements.

---

## ML Pipeline

| Metric | Value | Target |
|--------|-------|--------|
| F1 (fraud class) | **0.8526** | > 0.85 |
| AUC-ROC | **0.9772** | > 0.95 |
| Inference (model only) | **0.03ms** | < 5ms |
| SHAP explanation | **14ms** | < 100ms |
| Dataset | Kaggle Credit Card Fraud (284,807 rows, 492 fraud) | |
| Class ratio | 578:1 (imbalanced) | |
| Decision threshold | 0.76 (tuned for F1) | |

### Key Decisions

- **StandardScaler on Amount ONLY** — V1-V28 are already PCA-transformed
- **scale_pos_weight = 578** — handles class imbalance without SMOTE (which causes data leakage)
- **No SMOTE** — resampling on PCA features introduces synthetic data artifacts
- **Threshold tuning** — optimized for F1 on fraud class, not default 0.5
- **Never report accuracy** — baseline is 99.83% (always predict legit)

---

## Dashboard Features

- **Live transaction feed** — 2s polling with unmistakable fraud indicators
- **Fraud rows**: Red background + warning triangle icon (not color alone)
- **Legit rows**: Green tint + checkmark icon
- **Fraud alerts**: Real-time toast notifications when fraud is detected
- **SHAP waterfall** — click any transaction for explainability drawer
- **Risk gauge** — visual probability bar with color gradient
- **Stats bar** — total transactions, fraud rate, model F1, AUC-ROC with icons
- **Test form** — submit custom transactions or simulate demo data
- **Search & filter** — find transactions by amount or fraud/legit status
- **Dark fintech theme** — professional operations tool aesthetic

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML | Python, XGBoost, SHAP, scikit-learn, pandas |
| API | FastAPI, Pydantic, Uvicorn, SQLite, Rate Limiting |
| Frontend | React 18, TypeScript, Vite |
| Deploy | Docker Compose, nginx |
| Testing | pytest (35), Playwright (5) |

---

## Project Structure

```
├── api/                  # FastAPI backend
│   ├── main.py          # App + endpoints
│   ├── schemas.py       # Pydantic models
│   └── database.py      # SQLite storage
├── ml/                   # Machine learning
│   ├── training/        # Train XGBoost model
│   └── inference/       # Predict + SHAP explain
├── dashboard/            # React frontend
│   └── src/             # Components, API client
├── tests/                # Test suites
│   ├── test_api.py      # API endpoint tests
│   ├── test_ml.py       # ML model tests
│   ├── test_extended.py # Simulate, explain, edge cases
│   ├── test_latency.py  # Latency benchmarks
│   └── dashboard/       # Playwright E2E tests
├── docker-compose.yml   # Full stack deployment
└── requirements.txt     # Python dependencies
```

---

## Demo Script (for judges)

1. `docker compose up --build` — starts both services
2. Open http://localhost:5173 — see the live dashboard
3. In the test form, enter Amount: `1200`, V1: `-4.5`, V2: `-3.0` → Submit
4. See the transaction appear in the feed with fraud probability
5. Click any fraud row → SHAP explanation drawer opens
6. Open http://localhost:8000/docs — interactive Swagger UI
7. Try the `/stats` endpoint to see model metrics

---

## Compliance

- **EU AI Act Art.13**: SHAP explanations provide transparency for each prediction
- **SR 11-7**: Model validated with F1/AUC-ROC metrics, threshold tuning, and feature importance analysis
- **No accuracy metric**: Fraud is 0.17% of transactions — accuracy is meaningless

---

License: MIT
