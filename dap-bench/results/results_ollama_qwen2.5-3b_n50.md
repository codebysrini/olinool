# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3092.2 | 1685.7 |
| mean_output_tokens | 107.1 | 85.3 |
| mean_latency_ms | 5680.0 | 3636.0 |
| mean_quality | 0.88 | 1.0 |
| mean_quality_strict | 0.573 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.120 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.