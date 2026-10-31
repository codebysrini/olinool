# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4222.7 | 2240.9 |
| mean_output_tokens | 1261.3 | 1375.9 |
| mean_latency_ms | 27254.6 | 28323.6 |
| mean_quality | 0.98 | 0.893 |
| mean_quality_strict | 0.98 | 0.893 |
| injection_attempts | 17 | 17 |
| injection_successes | 1 | 2 |

**Input-token ratio A/B: 1.88×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.087 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 1/17 vs B 2/17 successful canary insertions.