# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3091.4 | 1659.6 |
| mean_output_tokens | 1756.1 | 1626.3 |
| mean_latency_ms | 42600.5 | 26539.4 |
| mean_quality | 0.3 | 0.66 |
| mean_quality_strict | 0.3 | 0.66 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.86×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.360 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.