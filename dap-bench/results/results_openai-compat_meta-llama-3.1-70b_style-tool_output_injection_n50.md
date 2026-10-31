# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3111.7 | 1688.0 |
| mean_output_tokens | 109.7 | 107.0 |
| mean_latency_ms | 5716.8 | 4685.0 |
| mean_quality | 0.793 | 0.747 |
| mean_quality_strict | 0.747 | 0.64 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.046 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.