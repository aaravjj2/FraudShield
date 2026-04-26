---
name: submission-check
description: Final checklist before submitting to any hackathon. Verify every required item is complete.
---
# Submission Checklist

Print PASS/FAIL for each item. Write results to reports/submission-check.txt.

**Technical:**
- curl http://localhost:8000/docs returns 200
- POST /predict returns fraud_score, is_fraud, confidence, top_features
- /latency-check passes (avg < 10ms)
- reports/metrics.json has F1 > 0.85 and AUC-ROC > 0.95
- docker-compose up -d succeeds
- Dashboard loads at localhost:5173 with no console errors
- All Playwright tests pass
- model.pkl NOT exposed via any API route

**Repository:**
- GitHub repo is public
- README has docker-compose up instructions
- Architecture diagram in README or docs/
- .env.example present, real .env in .gitignore
- creditcard.csv not in git history: `git log --all -- data/raw/creditcard.csv`

**Submission form (per hackathon):**
- Title: "FraudShield — Real-Time AI Fraud Detection API"
- Problem statement < 150 words with $34B statistic
- Tech stack: Python, XGBoost, SHAP, FastAPI, React, SQLite, Docker
- Model metrics pasted directly: F1, AUC-ROC, confusion matrix numbers
- 3-minute demo video link (Loom or YouTube Unlisted)
- Working prototype link from DEPLOY_URL.txt
- Architecture diagram attached
