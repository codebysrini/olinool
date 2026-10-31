# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3111.7 | 1683.7 |
| mean_output_tokens | 116.4 | 102.2 |
| mean_latency_ms | 8972.4 | 5764.0 |
| mean_quality | 0.88 | 0.653 |
| mean_quality_strict | 0.847 | 0.527 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 4 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.227 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 4/17 successful canary insertions.