# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3170.2 | 1735.3 |
| mean_output_tokens | 2254.2 | 1970.8 |
| mean_latency_ms | 27714.4 | 26121.1 |
| mean_quality | 1.0 | 0.913 |
| mean_quality_strict | 1.0 | 0.913 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.087 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.