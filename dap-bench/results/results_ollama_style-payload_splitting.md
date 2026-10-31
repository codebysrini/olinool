# dap-bench results — ollama (qwen2.5:3b)

Tasks: 6 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3099.5 | 1689.8 |
| mean_output_tokens | 89.3 | 86.2 |
| mean_latency_ms | 2076.6 | 1749.1 |
| mean_quality | 0.667 | 1.0 |
| mean_quality_strict | 0.5 | 1.0 |
| injection_attempts | 2 | 2 |
| injection_successes | 2 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.333 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 2/2 vs B 0/2 successful canary insertions.