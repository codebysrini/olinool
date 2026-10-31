# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3090.6 | 1685.0 |
| mean_output_tokens | 108.2 | 85.3 |
| mean_latency_ms | 2545.7 | 1881.5 |
| mean_quality | 0.78 | 1.0 |
| mean_quality_strict | 0.473 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.220 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.