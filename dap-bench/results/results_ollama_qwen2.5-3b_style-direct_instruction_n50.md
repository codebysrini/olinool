# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3090.2 | 1686.1 |
| mean_output_tokens | 104.7 | 86.6 |
| mean_latency_ms | 2453.6 | 1875.6 |
| mean_quality | 0.907 | 1.0 |
| mean_quality_strict | 0.693 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.093 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.