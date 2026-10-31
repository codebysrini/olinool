# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3087.2 | 1683.3 |
| mean_output_tokens | 99.4 | 85.3 |
| mean_latency_ms | 2233.8 | 1750.0 |
| mean_quality | 0.927 | 1.0 |
| mean_quality_strict | 0.773 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.073 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.