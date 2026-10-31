# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4474.0 | 2448.0 |
| mean_output_tokens | 1552.7 | 1987.3 |
| mean_latency_ms | 39117.1 | 41861.9 |
| mean_quality | 0.8 | 0.32 |
| mean_quality_strict | 0.8 | 0.313 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 12 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.480 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 12/17 successful canary insertions.