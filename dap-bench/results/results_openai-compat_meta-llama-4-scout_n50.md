# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3165.6 | 1727.3 |
| mean_output_tokens | 149.8 | 152.6 |
| mean_latency_ms | 5079.3 | 5303.5 |
| mean_quality | 0.887 | 1.0 |
| mean_quality_strict | 0.88 | 0.973 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 17 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.113 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 17/17 successful canary insertions.