# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3288.0 | 1853.7 |
| mean_output_tokens | 687.4 | 619.2 |
| mean_latency_ms | 1343.0 | 1236.9 |
| mean_quality | 0.933 | 0.873 |
| mean_quality_strict | 0.913 | 0.873 |
| injection_attempts | 17 | 17 |
| injection_successes | 4 | 0 |

**Input-token ratio A/B: 1.77×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.060 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 4/17 vs B 0/17 successful canary insertions.