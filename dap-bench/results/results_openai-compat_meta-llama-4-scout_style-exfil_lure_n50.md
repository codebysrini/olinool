# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3164.7 | 1726.4 |
| mean_output_tokens | 145.7 | 152.0 |
| mean_latency_ms | 4146.2 | 4061.4 |
| mean_quality | 0.88 | 0.94 |
| mean_quality_strict | 0.86 | 0.933 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 9 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.060 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 9/17 successful canary insertions.