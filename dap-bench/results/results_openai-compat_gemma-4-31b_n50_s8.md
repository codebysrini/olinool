# dap-bench results — openai-compat (gemma-4-31b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3088.2 | 1677.0 |
| mean_output_tokens | 84.3 | 84.0 |
| mean_latency_ms | 1158.4 | 1167.6 |
| mean_quality | 0.68 | 0.647 |
| mean_quality_strict | 0.68 | 0.647 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.033 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.