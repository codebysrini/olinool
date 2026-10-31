# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3107.8 | 1681.0 |
| mean_output_tokens | 110.6 | 105.4 |
| mean_latency_ms | 5666.5 | 5832.8 |
| mean_quality | 0.827 | 0.747 |
| mean_quality_strict | 0.78 | 0.627 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.