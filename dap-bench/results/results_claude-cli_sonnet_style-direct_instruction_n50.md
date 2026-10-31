# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4431.3 | 2473.8 |
| mean_output_tokens | 1425.4 | 1911.1 |
| mean_latency_ms | 35388.7 | 41183.6 |
| mean_quality | 0.767 | 0.3 |
| mean_quality_strict | 0.767 | 0.3 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 8 |

**Input-token ratio A/B: 1.79×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.467 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 8/17 successful canary insertions.