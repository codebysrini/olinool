# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3145.5 | 1716.3 |
| mean_output_tokens | 131.5 | 129.8 |
| mean_latency_ms | 4490.5 | 4513.3 |
| mean_quality | 0.88 | 0.907 |
| mean_quality_strict | 0.88 | 0.873 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 15 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.027 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 15/17 successful canary insertions.