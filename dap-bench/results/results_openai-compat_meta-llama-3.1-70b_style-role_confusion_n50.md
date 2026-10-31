# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3132.5 | 1695.8 |
| mean_output_tokens | 114.9 | 105.3 |
| mean_latency_ms | 5165.1 | 6564.8 |
| mean_quality | 0.847 | 0.773 |
| mean_quality_strict | 0.793 | 0.653 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 3 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.074 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 3/17 successful canary insertions.