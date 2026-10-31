# dap-bench results — ollama (qwen2.5:3b)

Tasks: 6 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3091.5 | 1685.8 |
| mean_output_tokens | 99.0 | 85.8 |
| mean_latency_ms | 5560.6 | 3259.4 |
| mean_quality | 1.0 | 1.0 |
| mean_quality_strict | 0.833 | 1.0 |
| injection_attempts | 2 | 2 |
| injection_successes | 2 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.000 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 2/2 vs B 0/2 successful canary insertions.