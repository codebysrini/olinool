# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3081.1 | 1671.5 |
| mean_output_tokens | 92.1 | 87.2 |
| mean_latency_ms | 12348.2 | 8106.9 |
| mean_quality | 0.747 | 0.513 |
| mean_quality_strict | 0.473 | 0.427 |
| injection_attempts | 17 | 17 |
| injection_successes | 13 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.234 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 13/17 vs B 0/17 successful canary insertions.