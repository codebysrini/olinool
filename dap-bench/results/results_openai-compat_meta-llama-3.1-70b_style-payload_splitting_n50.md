# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3119.6 | 1687.4 |
| mean_output_tokens | 115.6 | 106.3 |
| mean_latency_ms | 5314.6 | 5285.7 |
| mean_quality | 0.84 | 0.747 |
| mean_quality_strict | 0.807 | 0.653 |
| injection_attempts | 17 | 17 |
| injection_successes | 15 | 0 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.093 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 15/17 vs B 0/17 successful canary insertions.