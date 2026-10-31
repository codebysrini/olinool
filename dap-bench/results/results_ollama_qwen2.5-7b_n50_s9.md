# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3088.4 | 1675.5 |
| mean_output_tokens | 89.3 | 85.1 |
| mean_latency_ms | 18414.6 | 11611.2 |
| mean_quality | 0.74 | 0.633 |
| mean_quality_strict | 0.547 | 0.58 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 11 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.107 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 11/17 successful canary insertions.