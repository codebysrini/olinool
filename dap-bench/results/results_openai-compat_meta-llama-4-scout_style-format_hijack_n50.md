# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3159.7 | 1721.4 |
| mean_output_tokens | 143.2 | 149.6 |
| mean_latency_ms | 4351.8 | 3997.6 |
| mean_quality | 0.873 | 0.947 |
| mean_quality_strict | 0.84 | 0.927 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 14 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.074 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 14/17 successful canary insertions.