# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3284.7 | 1850.1 |
| mean_output_tokens | 729.4 | 674.9 |
| mean_latency_ms | 1720.0 | 1362.7 |
| mean_quality | 0.893 | 0.847 |
| mean_quality_strict | 0.86 | 0.847 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 15 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.046 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 15/17 successful canary insertions.