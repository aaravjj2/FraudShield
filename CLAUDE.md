# CLAUDE.md — FraudShield Agent OS
# Real-Time AI Fraud Detection API & Analytics Platform
# 5 hackathons | $18,350 prizes | Judges: Goldman Sachs · Citibank · ByteDance

## 🎯 Mission
Win all 5 target hackathons. Run 500 autonomous improvement iterations.
Every iteration: analyze → plan → build → test → review → compact → repeat.

Repo: https://github.com/aaravjj2/FraudShield

## 🔁 Default Behavior
No task given → run `/fraudshield-loop` immediately.
Compact after EVERY iteration. Auto-stop at 500.

## 🏗️ Stack
Backend:  Python · FastAPI · XGBoost · SHAP · SQLite · Docker
Frontend: React · TypeScript · Vite
ML:       Kaggle Credit Card Fraud (284,807 rows, 492 fraud)
Deploy:   Docker Compose · Railway · Vercel (dashboard)

## 🤖 Subagents (delegate, don't do everything yourself)
- `ml-engineer`       → ml/ directory, training, SHAP, metrics
- `security-reviewer` → after any API, CORS, or DB changes
- `frontend-agent`    → dashboard/ directory, UI, Playwright testids

## 🔌 MCPs
- github             → PRs, commits, issues
- playwright         → dashboard tests, screenshots
- memory             → persistent knowledge graph across 500 iterations
- context7           → live FastAPI/XGBoost/SHAP/React docs
- sequential-thinking → ML architecture reasoning

## 🧠 Karpathy Principles (hooks enforce these — not optional)
1. Think Before Coding — state assumptions before any line
2. Simplicity First — one clean POST request beats clever code
3. Surgical Changes — only touch files relevant to current task
4. Verify Everything — never claim < 10ms without /latency-check

## 🏆 Judging Criteria (Goldman Sachs / Citibank panels know ML)
1. Working demo — /predict live in browser, < 10ms, real response
2. SHAP explainability — judges know EU AI Act Art.13 and SR 11-7
3. Model quality — F1 > 0.85, AUC-ROC > 0.95, never report accuracy
4. Dashboard polish — real fintech operations tool, not student project
5. Developer UX — Swagger at /docs, integrate with one POST request
6. Architecture — clean 3-tier, Docker Compose, no spaghetti

## 📐 ML Rules (NEVER violate — these are enforced)
- Drop Time column (recording order, not real time)
- StandardScaler on Amount ONLY (V1–V28 already PCA-transformed)
- scale_pos_weight = 284315/492 ≈ 578 — NEVER use SMOTE (leakage)
- Report F1 on fraud class — accuracy baseline is 99.83% for useless model
- SHAP: TreeExplainer cached at module level, NEVER per-request
- model.pkl = model + scaler bundled — NEVER re-fit scaler at inference
- NEVER serve model.pkl via API endpoint

## ✅ Definition of Done
**ML:** F1 > 0.85, AUC-ROC > 0.95, inference < 5ms, SHAP < 1ms
**API:** POST /predict, GET /transactions, GET /stats, POST /batch — all < 10ms
        Swagger at /docs demo-ready. docker-compose up works.
**Dashboard:** Live 2s polling, red+icon fraud rows, SHAP waterfall,
               stats bar, demo form, all Playwright tests green
**Shipped:** /submission-check all green, all 5 hackathons submitted

## 🛑 Anti-Patterns (hooks block these)
- Serve model.pkl via API
- Use SMOTE
- Report accuracy as primary metric
- Claim < 10ms without /latency-check
- Commit creditcard.csv or .env
- Force-push to main
- Skip /compact between iterations
- Exceed 75% context without early compact

## 📝 Commits
feat: iter N — <one-line summary>
