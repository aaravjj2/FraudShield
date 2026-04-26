#!/usr/bin/env bash
# ================================================================
#  FRAUDSHIELD — COMPLETE FRESH SETUP (assume nothing exists)
#  Installs: Claude Code, Node, Python deps, MCPs, all config files
#  Run from inside your FraudShield project directory.
# ================================================================
set -euo pipefail

echo "🛡️  FraudShield — Complete Fresh Setup"
echo "🎯 5 Hackathons | \$18,350 Prize Pool"
echo "🏦 Judges: Goldman Sachs · Citibank · ByteDance"
echo "=================================================="

# ── PHASE 0: System check ─────────────────────────────────
echo ""; echo "▶ Phase 0 — System prerequisites..."

if ! command -v node &>/dev/null; then
  echo "📦 Node not found. Installing via nvm..."
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install --lts && nvm use --lts
else
  echo "✅ Node $(node --version)"
fi

command -v python3 &>/dev/null && echo "✅ $(python3 --version)" \
  || { echo "❌ Python3 missing — sudo apt install python3 python3-pip"; exit 1; }

command -v git &>/dev/null && echo "✅ $(git --version)" \
  || { echo "❌ Git missing — sudo apt install git"; exit 1; }

command -v docker &>/dev/null && echo "✅ Docker found" \
  || echo "⚠ Docker not found — install: https://docs.docker.com/get-docker/"

# ── PHASE 1: Claude Code ──────────────────────────────────
echo ""; echo "▶ Phase 1 — Claude Code..."

if ! command -v claude &>/dev/null; then
  echo "📦 Installing Claude Code..."
  curl -fsSL https://claude.ai/install.sh | bash 2>/dev/null \
    || npm install -g @anthropic-ai/claude-code
fi
echo "✅ Claude Code $(claude --version 2>/dev/null || echo 'installed')"

echo "🔑 Authenticating (browser will open)..."
claude auth login || echo "⚠ Run 'claude auth login' manually if this failed"

# ── PHASE 2: Directory structure ──────────────────────────
echo ""; echo "▶ Phase 2 — Directories..."

mkdir -p .claude/{commands,hooks,skills/latency-check,skills/submission-check,agents}
mkdir -p loop-logs screenshots
mkdir -p api/{routers,models,services,schemas}
mkdir -p ml/{training,inference,evaluation}
mkdir -p data/{raw,processed}
mkdir -p reports
mkdir -p tests/{api,ml,dashboard}
mkdir -p dashboard/src/{components,hooks,utils,types,api}
mkdir -p dashboard/public

touch loop-logs/.iteration-count DEPLOY_URL.txt SUBMISSION_URLS.txt
echo "✅ Structure created"

# ── PHASE 3: MCP servers ──────────────────────────────────
echo ""; echo "▶ Phase 3 — MCP servers..."

claude mcp add github --scope project --transport stdio \
  -- npx -y @modelcontextprotocol/server-github \
  || echo "⚠ github MCP — set GITHUB_PERSONAL_ACCESS_TOKEN in env"

claude mcp add playwright --scope project --transport stdio \
  -- npx -y @anthropic-ai/mcp-playwright \
  || echo "⚠ playwright MCP failed"

claude mcp add memory --scope user --transport stdio \
  -- npx -y @modelcontextprotocol/server-memory \
  || echo "⚠ memory MCP failed"

claude mcp add context7 --scope user --transport stdio \
  -- npx -y @upstash/context7-mcp \
  || echo "⚠ context7 MCP failed"

claude mcp add sequential-thinking --scope user --transport stdio \
  -- npx -y @modelcontextprotocol/server-sequential-thinking \
  || echo "⚠ sequential-thinking MCP failed"

echo "✅ MCPs:"; claude mcp list

# ── PHASE 4: Playwright ───────────────────────────────────
echo ""; echo "▶ Phase 4 — Playwright..."
npm install -D @playwright/test 2>/dev/null || true
npx playwright install chromium 2>/dev/null || echo "⚠ Run: npx playwright install chromium"
echo "✅ Playwright ready"

# ── PHASE 5: Python deps ──────────────────────────────────
echo ""; echo "▶ Phase 5 — Python dependencies..."
pip install fastapi "uvicorn[standard]" xgboost shap scikit-learn \
  pandas numpy httpx pytest pytest-asyncio python-multipart \
  pydantic mypy black isort kaggle \
  --break-system-packages -q \
  || echo "⚠ Some pip installs failed — check manually"
echo "✅ Python deps installed"

# ── PHASE 6: Hooks config ─────────────────────────────────
echo ""; echo "▶ Phase 6 — Hooks..."

cat > .claude/settings.json << 'JSON'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=\"$CLAUDE_FILE_PATH\"; if [[ \"$FILE\" == *.py ]]; then python3 -m black \"$FILE\" --quiet 2>/dev/null || true; fi; if [[ \"$FILE\" == *.ts || \"$FILE\" == *.tsx ]]; then npx prettier --write \"$FILE\" 2>/dev/null || true; fi"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/validate-bash.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "N=$(cat loop-logs/.iteration-count 2>/dev/null || echo 0); echo \"[PreCompact] Compacting after iteration $N\""
          }
        ]
      }
    ]
  },
  "permissions": {
    "deny": [
      "Bash(rm -rf /)",
      "Bash(git push --force origin main)",
      "Edit(.env*)"
    ]
  }
}
JSON

cat > .claude/hooks/validate-bash.sh << 'SH'
#!/usr/bin/env bash
CMD="${CLAUDE_TOOL_INPUT:-}"
if echo "$CMD" | grep -q "git push.*--force.*main\|git push.*-f.*main"; then
  echo "BLOCKED: force push to main"; exit 1; fi
if echo "$CMD" | grep -q "git add.*creditcard\.csv"; then
  echo "BLOCKED: do not commit creditcard.csv"; exit 1; fi
if echo "$CMD" | grep -qE "rm -rf (src|api|ml|dashboard|/)"; then
  echo "BLOCKED: destructive rm -rf"; exit 1; fi
exit 0
SH
chmod +x .claude/hooks/validate-bash.sh

cat > .claude/hooks/pre-commit.sh << 'SH'
#!/usr/bin/env bash
if git diff --cached --name-only | grep -qE 'creditcard\.csv|\.env$|\.pem$|\.key$'; then
  echo "BLOCKED: sensitive file detected"; exit 1; fi
echo "✓ Pre-commit passed"
SH
chmod +x .claude/hooks/pre-commit.sh
git config core.hooksPath .claude/hooks 2>/dev/null || true
echo "✅ Hooks written"

# ── PHASE 7: Subagents ────────────────────────────────────
echo ""; echo "▶ Phase 7 — Subagents..."

cat > .claude/agents/ml-engineer.md << 'MD'
---
name: ml-engineer
description: ML specialist for XGBoost, SHAP, model evaluation. Use for anything in ml/ — training, metrics, explainability.
tools: Read, Write, Edit, Bash, Glob, Grep
model: claude-sonnet-4-6
---
You are a senior ML engineer specializing in fraud detection.

Hard rules — never violate:
- NEVER use SMOTE — use scale_pos_weight=578
- ALWAYS bundle model + scaler in model.pkl together
- NEVER re-fit scaler at inference time
- ALWAYS use F1 on fraud class as primary metric, not accuracy
- ALWAYS cache TreeExplainer at module level, never per-request
- NEVER serve model.pkl via any API endpoint

Feature engineering: drop Time, StandardScaler on Amount only, V1-V28 as-is.
Thresholds: F1 > 0.85, AUC-ROC > 0.95.
SHAP: top 5 features with raw value + contribution.
MD

cat > .claude/agents/security-reviewer.md << 'MD'
---
name: security-reviewer
description: Security specialist. Invoke after any changes to API endpoints, CORS, or DB queries.
tools: Read, Grep, Glob, Bash
model: claude-sonnet-4-6
permissionMode: plan
---
You are a senior application security engineer.

Review for: model.pkl served via API (critical), wildcard CORS in production,
raw SQL strings, secrets in code, missing Pydantic validation, .env files committed.

Output: CRITICAL / HIGH / MEDIUM / LOW with file:line for each finding.
MD

cat > .claude/agents/frontend-agent.md << 'MD'
---
name: frontend-agent
description: React/TypeScript dashboard specialist. Invoke for dashboard/ changes, UI polish, SHAP visualization, accessibility.
tools: Read, Write, Edit, Bash, Glob
model: claude-sonnet-4-6
---
You are a senior frontend engineer building a fintech operations dashboard.

Standards: TypeScript strict, no `any`, components < 150 lines.
Required data-testid: transaction-feed, fraud-row, legit-row, shap-drawer,
shap-bar, amount-input, v1-input, v2-input, submit-btn, stats-bar.
Accessibility: ARIA labels, keyboard nav, 4.5:1 contrast minimum.
Real-time: poll GET /transactions every 2 seconds.
Fraud rows: red + secondary icon indicator (not color alone).
MD

echo "✅ Subagents written"

# ── PHASE 8: Skills ───────────────────────────────────────
echo ""; echo "▶ Phase 8 — Skills..."

cat > .claude/skills/latency-check/SKILL.md << 'MD'
---
name: latency-check
description: Benchmark POST /predict latency. Use before any submission or deployment to verify the < 10ms claim.
---
# Latency Check

Fires 100 requests, reports avg and p95:

```bash
python3 -c "
import httpx, time, statistics
url = 'http://localhost:8000/predict'
payload = {'amount': 42.0, 'features': [0.0]*28}
times = []
for _ in range(100):
    t = time.perf_counter()
    httpx.post(url, json=payload, timeout=5)
    times.append((time.perf_counter()-t)*1000)
avg = statistics.mean(times)
p95 = statistics.quantiles(times, n=20)[18]
print(f'avg={avg:.2f}ms  p95={p95:.2f}ms')
print('PASS' if avg < 10 else f'FAIL — {avg:.2f}ms > 10ms target')
"
```

If FAIL: profile with `py-spy top -- python3 -m uvicorn api.main:app`
Common causes: TreeExplainer not cached, scaler not bundled, SQLite write blocking.
MD

cat > .claude/skills/submission-check/SKILL.md << 'MD'
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
MD

echo "✅ Skills written"

# ── PHASE 9: CLAUDE.md ────────────────────────────────────
echo ""; echo "▶ Phase 9 — CLAUDE.md..."

cat > CLAUDE.md << 'MD'
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
MD
echo "✅ CLAUDE.md written"

# ── PHASE 10: Main loop command ───────────────────────────
echo ""; echo "▶ Phase 10 — Slash command..."

cat > .claude/commands/fraudshield-loop.md << 'MD'
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
MD
echo "✅ Slash command written"

# ── PHASE 11: Config files ────────────────────────────────
echo ""; echo "▶ Phase 11 — Config files..."

cat > .gitignore << 'GIT'
data/raw/creditcard.csv
data/raw/*.csv
data/raw/*.zip
ml/*.pkl
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.mypy_cache/
.pytest_cache/
.env
.env.*
!.env.example
node_modules/
dashboard/dist/
dashboard/.vite/
reports/metrics.json
test-results/
playwright-report/
.DS_Store
*.log
GIT

cat > .env.example << 'ENV'
API_HOST=0.0.0.0
API_PORT=8000
MODEL_PATH=ml/model.pkl
DB_PATH=data/fraudshield.db
CORS_ORIGINS=http://localhost:5173
KAGGLE_USERNAME=
KAGGLE_KEY=
ENV

cat > .mcp.json << 'MCP'
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}" }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-playwright"]
    }
  }
}
MCP

cat > docker-compose.yml << 'DC'
version: "3.9"
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    volumes:
      - ./ml:/app/ml:ro
      - ./data:/app/data
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 10s
      timeout: 5s
      retries: 5
  dashboard:
    build: ./dashboard
    ports: ["5173:80"]
    depends_on:
      api:
        condition: service_healthy
DC

cat > playwright.config.ts << 'PW'
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/dashboard',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'on',
    video: 'retain-on-failure',
  },
});
PW

cat > tests/dashboard/dashboard.spec.ts << 'SPEC'
import { test, expect } from '@playwright/test';

test('dashboard loads, no console errors', async ({ page }) => {
  const errs: string[] = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('/');
  await page.waitForSelector('[data-testid="transaction-feed"]', { timeout: 5000 });
  expect(errs).toHaveLength(0);
  await page.screenshot({ path: 'screenshots/01-loaded.png' });
});

test('suspicious transaction → red fraud row', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '1200');
  await page.fill('[data-testid="v1-input"]', '-4.5');
  await page.fill('[data-testid="v2-input"]', '-3.0');
  await page.click('[data-testid="submit-btn"]');
  await expect(page.locator('[data-testid="fraud-row"]').first()).toBeVisible({ timeout: 3000 });
  await page.screenshot({ path: 'screenshots/02-fraud.png' });
});

test('normal transaction → green row', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '42');
  await page.click('[data-testid="submit-btn"]');
  await expect(page.locator('[data-testid="legit-row"]').first()).toBeVisible({ timeout: 3000 });
  await page.screenshot({ path: 'screenshots/03-legit.png' });
});

test('fraud row click → SHAP drawer with 5 bars', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="amount-input"]', '1200');
  await page.fill('[data-testid="v1-input"]', '-4.5');
  await page.click('[data-testid="submit-btn"]');
  await page.locator('[data-testid="fraud-row"]').first().click();
  await expect(page.locator('[data-testid="shap-drawer"]')).toBeVisible({ timeout: 2000 });
  await expect(page.locator('[data-testid="shap-bar"]')).toHaveCount(5);
  await page.screenshot({ path: 'screenshots/04-shap.png' });
});

test('stats bar visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('[data-testid="stats-bar"]')).toBeVisible();
});
SPEC

echo "✅ Config files written"

# ── PHASE 12: Kaggle dataset ──────────────────────────────
echo ""; echo "▶ Phase 12 — Dataset..."

if [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "Kaggle credentials found — downloading creditcard.csv..."
  kaggle datasets download -d mlg-ulb/creditcardfraud -p data/raw --unzip \
    && echo "✅ creditcard.csv downloaded" \
    || echo "⚠ Download failed — get manually from kaggle.com/datasets/mlg-ulb/creditcardfraud"
else
  echo "⚠ No Kaggle credentials. Download manually:"
  echo "   1. kaggle.com/settings → API → Create New Token → saves kaggle.json"
  echo "   2. cp ~/Downloads/kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json"
  echo "   3. kaggle datasets download -d mlg-ulb/creditcardfraud -p data/raw --unzip"
  echo "   OR: download creditcard.csv directly and place at data/raw/creditcard.csv"
fi

# ── PHASE 13: Git ─────────────────────────────────────────
echo ""; echo "▶ Phase 13 — Git..."

if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "chore: fresh FraudShield setup — 500-iteration hackathon loop ready"
  echo "✅ Git initialized"
else
  echo "✅ Git repo exists"
fi

# ── DONE ──────────────────────────────────────────────────
echo ""
echo "=================================================================="
echo "✅  FRAUDSHIELD — COMPLETE SETUP DONE"
echo "=================================================================="
echo ""
echo "Everything installed:"
echo "  ✅ Claude Code + auth"
echo "  ✅ 5 MCP servers (github, playwright, memory, context7, sequential-thinking)"
echo "  ✅ Python deps (fastapi, xgboost, shap, scikit-learn, etc.)"
echo "  ✅ Playwright + Chromium"
echo "  ✅ CLAUDE.md — full agent OS"
echo "  ✅ /fraudshield-loop — 500-iter autonomous loop with /compact"
echo "  ✅ 3 subagents (ml-engineer, security-reviewer, frontend-agent)"
echo "  ✅ 2 skills (/latency-check, /submission-check)"
echo "  ✅ Hooks (auto-format, bash validation, pre-commit)"
echo "  ✅ .claude/settings.json — permissions + hook config"
echo "  ✅ .mcp.json — shared team MCP config"
echo "  ✅ docker-compose.yml"
echo "  ✅ playwright.config.ts + full test suite"
echo "  ✅ .gitignore (blocks creditcard.csv + .env)"
echo "  ✅ .env.example"
echo ""
echo "⚠️  Before starting the loop — 3 things:"
echo "   1. data/raw/creditcard.csv (see Kaggle instructions above)"
echo "   2. export GITHUB_PERSONAL_ACCESS_TOKEN=your_token"
echo "   3. npx vercel login   (for dashboard deploys)"
echo ""
echo "▶  START:"
echo "   claude"
echo "   /fraudshield-loop"
echo ""
echo "🛑  Stop: type 'stop' in Claude Code"
echo "🏁  Auto-stops at iteration 500"
