# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4385.7 | 2472.1 |
| mean_output_tokens | 1189.6 | 1824.8 |
| mean_latency_ms | 43405.6 | 42161.5 |
| mean_quality | 0.82 | 0.44 |
| mean_quality_strict | 0.82 | 0.44 |
| injection_attempts | 17 | 17 |
| injection_successes | 15 | 13 |

**Input-token ratio A/B: 1.77×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.380 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 15/17 vs B 13/17 successful canary insertions.