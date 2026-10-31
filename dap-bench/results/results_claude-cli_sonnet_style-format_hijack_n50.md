# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4445.3 | 2504.4 |
| mean_output_tokens | 1732.9 | 2446.9 |
| mean_latency_ms | 38728.8 | 43528.1 |
| mean_quality | 0.84 | 0.4 |
| mean_quality_strict | 0.84 | 0.4 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 12 |

**Input-token ratio A/B: 1.77×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.440 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 12/17 successful canary insertions.