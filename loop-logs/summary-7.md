# Iter 7 of 500 — Summary

## State
- Endpoints: 7 working, /explain now returns base_value + base_probability
- Tests: 13/13 pytest passing
- Model: F1=0.8526, AUC-ROC=0.9772
- SHAP: Waterfall chart with base value → contributions → final prediction
- Simulate: Guarantees 2 fraud transactions from real dataset samples

## What Was Built
- SHAP waterfall chart: base value row, feature contribution rows, final prediction row
- Plain English explanation text below the chart
- /explain endpoint returns base_value (log-odds) and base_probability
- /simulate guarantees fraud using real fraud samples with noise

## What FAILED and WHY
- Docker created data/fraudshield.db as root → SQLite readonly errors after Docker down
  Fix: rm -f data/fraudshield.db* before running tests
- Port 8000 zombie process from Docker → had to use port 8001 for testing
  Fix: need to properly stop Docker containers before switching to local dev
- Vite started from wrong CWD → use subshell `(cd dir && vite)` pattern

## Completion: ~98% of Definition of Done
All core features working. Only remaining: live deploy URL.

## Most Important for Iter 8
Push latest to GitHub. Run full Playwright E2E with new SHAP waterfall. Consider adding more test coverage for /explain and /simulate endpoints.
