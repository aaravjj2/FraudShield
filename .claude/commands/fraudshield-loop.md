# /fraudshield-loop
Run for exactly 500 iterations. Stop early ONLY if user says "stop" or "exit".

Context: FraudShield — AI Fraud Detection API & Dashboard
Stack: Python · XGBoost · SHAP · FastAPI · React · Docker
Target: Win 5 concurrent hackathons. Judges: Goldman Sachs, Citibank, ByteDance.

---

**Before every iteration:**
```bash
COUNT=$(cat ./loop-logs/.iteration-count 2>/dev/null || echo 0); N=$((COUNT + 1))
echo "Iteration $N / 500"
```
Read ALL ./loop-logs/summary-*.md — recall full history, avoid repeating failures.
Check DEPLOY_URL.txt. Probe live API if it exists.

---

## STEP 1 — Autonomous Analysis + Plan

You are a senior ML engineer AND a Goldman Sachs quant judging this submission.
Do NOT blindly follow the PRD. Think independently.

Ask yourself:
- What is the SINGLE biggest gap between current state and winning?
- Would a Citibank judge be impressed by the SHAP output right now?
- Is the < 10ms latency claim actually benchmarked?
- Does the dashboard look like a real fintech tool or a student project?
- Is anything broken that makes a judge close the tab immediately?
- What is NOT in the PRD that would dramatically improve the score?
- What did previous iterations fail at — how do we not repeat that?

Use **sequential-thinking MCP** for complex ML/architecture decisions.
Use **context7 MCP** to verify FastAPI, XGBoost, SHAP, React APIs before writing.

Write ITERATION PLAN → ./loop-logs/plan-$N.md:
- Current state (what works, broken, missing)
- One highest-leverage improvement
- Exact files to change
- How you will verify success

PRD is a reference, not a ceiling. If something better emerges, build it and update PRD.

## STEP 2 — Self-Verify

Review as the strictest judge. FAIL if:
- Vague plan with no file paths
- Ignores critical bug in favor of polish
- Introduces SMOTE, serves model.pkl via API, re-fits scaler at inference
- Claims < 10ms without a benchmark plan
- Repeats a previous iteration exactly
- Unmeasurable success criteria

If FAIL: rewrite plan. Repeat until PASS.

## STEP 3 — Build

Execute completely. No half-measures.

Delegate via subagents:
- ml/ changes → `ml-engineer` agent
- dashboard/ changes → `frontend-agent` agent
- After API/CORS/DB changes → `security-reviewer` agent

Autonomous rules:
- Fix bugs found along the way
- If better idea emerges mid-build, adapt and log why
- If PRD spec is wrong in practice, update both code and PRD

Standards:
- Python: type hints, no bare except, docstrings
- FastAPI: Pydantic on ALL inputs/outputs
- React: TypeScript strict, no `any`, all data-testid attributes present
- SHAP: TreeExplainer at module level — never per-request

```bash
git add -A && git commit -m "feat: iter $N — <what changed>"
```

## STEP 4 — Test + Benchmark

Fix every failure before continuing.

```bash
# Type check
mypy api/ ml/ --ignore-missing-imports 2>&1 | tee ./loop-logs/mypy-$N.txt || true

# Unit + integration
pytest tests/ -v 2>&1 | tee ./loop-logs/pytest-$N.txt

# Latency — /latency-check skill
# Run /latency-check and save output to loop-logs/latency-$N.txt

# ML model regression (if model.pkl exists)
python3 -c "
import pickle, numpy as np, os
if not os.path.exists('ml/model.pkl'): print('model.pkl not built yet'); exit(0)
bundle = pickle.load(open('ml/model.pkl','rb'))
model, scaler = bundle['model'], bundle['scaler']
assert 0 <= model.predict_proba([[0]*29])[0][1] <= 1
fixed = np.array([[1200.0,-4.5,-3.0]+[0.0]*26])
score = model.predict_proba(np.hstack([scaler.transform(fixed[:,:1]), fixed[:,1:]]))[0][1]
print(f'Suspicious: {score:.4f}')
assert score > 0.5, f'Score {score:.4f} too low — check model'
print('MODEL PASS')
" 2>&1 | tee ./loop-logs/model-$N.txt

# Playwright dashboard
npx playwright test tests/dashboard/ --reporter=list 2>&1 \
  | tee ./loop-logs/playwright-$N.txt || echo "⚠ Dashboard tests failed"
```

Save screenshots → ./screenshots/

## STEP 5 — Quality Review + Status + Deploy

**API review:**
```bash
curl -s http://localhost:8000/docs | grep -q "FraudShield" && echo "Swagger OK"
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"amount":1200,"features":[-4.5,-3.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}' \
  | python3 -m json.tool
```

**Dashboard review:** Look at screenshots. Check:
- Fraud rows: unmistakably red WITH secondary icon (not color alone)
- SHAP chart: readable to a non-ML person
- Overall feel: real fintech tool, not student project
Fix anything that fails BEFORE writing status.

**Write ./loop-logs/status-$N.md:**
- What was built, what changed
- pytest / latency / Playwright results
- Model metrics if retrained
- Honest: "right now this would rank ___"
- Top 3 for next iteration

**Run /submission-check skill — paste results in status log.**

**Deploy:**
```bash
npm run build --prefix dashboard 2>/dev/null \
  && npx vercel --prod --yes --cwd dashboard 2>/dev/null \
  && echo "Deployed" >> DEPLOY_URL.txt \
  || echo "⚠ Deploy failed"
```

## STEP 6 — Compact + Counter + Loop

**Write ./loop-logs/summary-$N.md:**
- Iter $N of 500
- Exact state: endpoints, test pass rates, current F1/latency
- What was built and whether it worked
- What FAILED and WHY (prevent repetition)
- Completion % toward Definition of Done
- Single most important thing for N+1

**Update counter:**
```bash
echo $N > ./loop-logs/.iteration-count
```

**MANDATORY /compact — every single iteration, no exceptions.**
Context freshness is critical across 500 iterations.

**Loop check:**
```bash
[ "$N" -ge 500 ] \
  && echo "✅ 500 iterations complete." && cat ./loop-logs/summary-500.md \
  || echo "Restarting → iteration $((N+1))"
```

If N < 500: restart at STEP 1 immediately.
Stop early ONLY if user says "stop" or "exit".
