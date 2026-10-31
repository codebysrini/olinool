# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3110.3 | 1687.8 |
| mean_output_tokens | 134.5 | 109.8 |
| mean_latency_ms | 26475.2 | 17232.4 |
| mean_quality | 0.833 | 0.727 |
| mean_quality_strict | 0.567 | 0.453 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.106 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.