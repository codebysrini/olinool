# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4219.4 | 2252.4 |
| mean_output_tokens | 1372.9 | 1414.1 |
| mean_latency_ms | 27595.6 | 27826.1 |
| mean_quality | 0.96 | 0.84 |
| mean_quality_strict | 0.96 | 0.84 |
| injection_attempts | 17 | 17 |
| injection_successes | 2 | 1 |

**Input-token ratio A/B: 1.87×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.120 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 2/17 vs B 1/17 successful canary insertions.