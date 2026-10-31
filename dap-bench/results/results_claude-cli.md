# dap-bench results — claude-cli (haiku)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 30.0 | 30.0 |
| mean_output_tokens | 1163.4 | 1018.8 |
| mean_latency_ms | 19335.2 | 16647.7 |
| mean_quality | 0.972 | 1.0 |
| mean_quality_strict | 0.972 | 1.0 |
| injection_attempts | 4 | 4 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.00×** — scoped views cut context by 0% on this suite.
Quality delta (B − A): +0.028 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/4 vs B 0/4 successful canary insertions.