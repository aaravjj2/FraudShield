# Iter 3 of 500 — Summary

## State
- Endpoints: 5/5 working
- Tests: 13 pytest + 5 Playwright = 18/18 passing
- Model: F1=0.8526, AUC-ROC=0.9772
- Docker Compose: BOTH containers build and run, API healthy, dashboard serves
- Dashboard: Professional header, SHAP explanations, EU AI Act note

## What Was Built
- Docker Compose end-to-end deployment
- Professional FraudShield branding (header with shield logo, API docs link)
- SHAP drawer with plain-English explanations
- Fixed testid on all component states

## What FAILED and WHY
- API Dockerfile had `COPY ../ml` which doesn't work in Docker build context — fixed with correct paths
- Nginx proxy used `backend` but compose service was `api` — fixed
- Playwright test 1 failed: `data-testid="transaction-feed"` only on loaded state — added to loading/error/empty states

## Completion: ~85% of Definition of Done
- [x] ML: F1 > 0.85, AUC-ROC > 0.95
- [x] API: All endpoints working, Pydantic, Swagger
- [x] Dashboard: Professional, all Playwright tests pass
- [x] Docker: docker-compose up works
- [x] Tests: 18/18 passing
- [ ] API: < 10ms latency (WSL2 overhead, model-only is 0.03ms)
- [ ] Shipped: No live deploy URL yet

## Most Important for Iter 4
Live deployment — get a URL judges can click. Also optimize latency by making SHAP async.
