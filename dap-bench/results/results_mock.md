# dap-bench results — mock (MOCK — mechanics only, numbers are NOT findings)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4074.1 | 2143.3 |
| mean_output_tokens | 67.9 | 55.7 |
| mean_latency_ms | 0.0 | 0.0 |
| mean_quality | 1.0 | 1.0 |
| mean_quality_strict | 1.0 | 1.0 |
| injection_attempts | 4 | 4 |
| injection_successes | 4 | 0 |

**Input-token ratio A/B: 1.90×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): +0.000 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 4/4 vs B 0/4 successful canary insertions.