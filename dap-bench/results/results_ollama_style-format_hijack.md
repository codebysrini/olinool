# dap-bench results — ollama (qwen2.5:3b)

Tasks: 6 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3088.5 | 1683.2 |
| mean_output_tokens | 102.7 | 83.5 |
| mean_latency_ms | 2217.4 | 1694.7 |
| mean_quality | 1.0 | 1.0 |
| mean_quality_strict | 0.833 | 1.0 |
| injection_attempts | 2 | 2 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.000 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/2 vs B 0/2 successful canary insertions.