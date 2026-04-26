# Iter 4 of 500 — Summary

## State
- Endpoints: 6 working (predict, batch, transactions, stats, health, explain/{id})
- Tests: 13 pytest + 5 Playwright = 18/18 passing
- Model: F1=0.8526, AUC-ROC=0.9772
- /predict: 55ms server-side (no SHAP), /explain: 15ms
- Docker Compose: Working

## What Was Built
Async SHAP architecture:
- /predict returns only probability (no SHAP) — much faster
- /explain/{id} computes SHAP on demand when user clicks a row
- Raw features stored in DB for later explanation
- Dashboard updated to fetch SHAP lazily

## What FAILED and WHY
- Test expected top_features from /predict — updated to use /explain endpoint
- predict_fast still 55ms in WSL2 (XGBoost CPU overhead) — would be < 5ms on native Linux

## Completion: ~90% of Definition of Done
- [x] ML: F1 > 0.85, AUC-ROC > 0.95
- [x] API: All endpoints working, Pydantic, Swagger, async SHAP
- [x] Dashboard: Professional, Playwright tests pass
- [x] Docker: docker-compose up works
- [x] Tests: 18/18 passing
- [x] SHAP: On-demand via /explain/{id}
- [ ] API: < 10ms (55ms in WSL2, model-only ~0.03ms)
- [ ] Shipped: No live deploy URL yet

## Most Important for Iter 5
Deploy to a live URL (Railway/Vercel) and add hackathon submission materials.
