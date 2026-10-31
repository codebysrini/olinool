# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3160.9 | 1726.5 |
| mean_output_tokens | 148.3 | 154.4 |
| mean_latency_ms | 5111.7 | 5602.4 |
| mean_quality | 0.933 | 0.973 |
| mean_quality_strict | 0.907 | 0.967 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 15 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.040 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 15/17 successful canary insertions.