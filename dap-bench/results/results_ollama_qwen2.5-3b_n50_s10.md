# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3092.3 | 1685.8 |
| mean_output_tokens | 108.7 | 85.7 |
| mean_latency_ms | 5735.0 | 3603.8 |
| mean_quality | 0.893 | 1.0 |
| mean_quality_strict | 0.613 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.107 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.