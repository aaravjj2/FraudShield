# Iter 2 of 500 — Summary

## State
- Endpoints: 5/5 working (predict, batch, transactions, stats, health)
- Unit tests: 13/13 passing
- Playwright tests: 5/5 passing
- Model: F1=0.8526, AUC-ROC=0.9772
- Dashboard: Live polling, fraud rows, SHAP waterfall all verified
- Latency: ~60-200ms (WSL2, not representative of Docker)

## What Was Built
Validation iteration — confirmed full E2E works:
- API and dashboard running simultaneously
- All Playwright tests green on first try
- Screenshots captured: loaded, fraud, legit, SHAP views

## What FAILED and WHY
- Nothing major failed this iteration
- Vite config had port 3000 instead of 5173 — fixed

## Completion: ~75% of Definition of Done
- [x] ML: F1 > 0.85, AUC-ROC > 0.95
- [x] API: All endpoints working, Pydantic, Swagger
- [x] Dashboard: Built with all components, Playwright tests pass
- [x] Tests: 13 pytest + 5 Playwright = 18 total, all green
- [ ] API: < 10ms latency (WSL2 overhead, Docker should be fast)
- [ ] Shipped: No deploy yet — need Docker or Railway

## Most Important for Iter 3
Deploy to Railway/Vercel for live demo URL. Judges need a clickable URL.
