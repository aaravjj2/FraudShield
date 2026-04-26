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
