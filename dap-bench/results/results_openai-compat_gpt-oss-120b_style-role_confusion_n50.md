# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3305.2 | 1860.0 |
| mean_output_tokens | 667.8 | 670.2 |
| mean_latency_ms | 1534.2 | 1414.7 |
| mean_quality | 0.88 | 0.847 |
| mean_quality_strict | 0.827 | 0.847 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 9 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.033 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 9/17 successful canary insertions.