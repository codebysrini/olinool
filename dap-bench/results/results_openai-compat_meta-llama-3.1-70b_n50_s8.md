# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3116.6 | 1695.9 |
| mean_output_tokens | 114.5 | 111.8 |
| mean_latency_ms | 4723.3 | 4464.7 |
| mean_quality | 0.827 | 0.653 |
| mean_quality_strict | 0.773 | 0.493 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.174 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.