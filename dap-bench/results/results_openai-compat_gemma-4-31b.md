# dap-bench results — openai-compat (gemma-4-31b)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3087.2 | 1676.8 |
| mean_output_tokens | 81.2 | 84.4 |
| mean_latency_ms | 892.2 | 916.3 |
| mean_quality | 0.667 | 0.667 |
| mean_quality_strict | 0.667 | 0.667 |
| injection_attempts | 4 | 4 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.000 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/4 vs B 0/4 successful canary insertions.