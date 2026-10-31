# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3170.4 | 1726.5 |
| mean_output_tokens | 151.1 | 153.7 |
| mean_latency_ms | 4345.9 | 4250.0 |
| mean_quality | 0.873 | 1.0 |
| mean_quality_strict | 0.86 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 16 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.127 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 16/17 successful canary insertions.