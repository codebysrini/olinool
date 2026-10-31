# dap-bench results — ollama (qwen2.5:3b)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3091.6 | 1695.1 |
| mean_output_tokens | 107.9 | 85.3 |
| mean_latency_ms | 5487.3 | 3322.8 |
| mean_quality | 0.861 | 1.0 |
| mean_quality_strict | 0.583 | 1.0 |
| injection_attempts | 4 | 4 |
| injection_successes | 4 | 0 |

**Input-token ratio A/B: 1.82×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.139 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 4/4 vs B 0/4 successful canary insertions.