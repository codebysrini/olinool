# dap-bench results — openai-compat (gemma-4-31b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3088.6 | 1677.3 |
| mean_output_tokens | 83.9 | 84.0 |
| mean_latency_ms | 1155.4 | 1214.2 |
| mean_quality | 0.687 | 0.653 |
| mean_quality_strict | 0.687 | 0.653 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.034 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.