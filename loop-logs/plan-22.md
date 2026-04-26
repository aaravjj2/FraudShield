# Iteration 22 Plan — Rate Limiting + Fraud Alert Toast

## Current State
- 27/27 tests passing, F1=0.8526, AUC-ROC=0.9772
- 8 API endpoints, Docker Compose works
- Dashboard has search/filter, SHAP waterfall, live polling
- Missing: production middleware, visual alert system

## Improvement: Rate Limiting + Fraud Alert Notifications
Shows Goldman Sachs judges production-awareness and makes the dashboard feel like a real SOC tool.

## Files to Change
1. `api/middleware.py` — Add RateLimitMiddleware (sliding window, 60 req/min)
2. `api/main.py` — Register rate limit middleware
3. `dashboard/src/components/FraudAlert.tsx` — New: toast notification for fraud
4. `dashboard/src/App.tsx` — Integrate fraud alerts with polling
5. `dashboard/src/App.css` — Alert styling

## Verification
- pytest 27/27
- Rate limit returns 429 after 60 requests
- Dashboard shows toast on fraud detection
