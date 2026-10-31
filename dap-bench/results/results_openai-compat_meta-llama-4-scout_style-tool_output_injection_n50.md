# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3162.0 | 1725.7 |
| mean_output_tokens | 145.0 | 150.1 |
| mean_latency_ms | 5209.9 | 4889.5 |
| mean_quality | 0.853 | 0.987 |
| mean_quality_strict | 0.84 | 0.973 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 1 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.134 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 1/17 successful canary insertions.