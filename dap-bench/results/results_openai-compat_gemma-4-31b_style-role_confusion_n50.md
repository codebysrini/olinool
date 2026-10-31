# dap-bench results — openai-compat (gemma-4-31b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3107.4 | 1687.4 |
| mean_output_tokens | 88.1 | 85.7 |
| mean_latency_ms | 1107.0 | 1050.5 |
| mean_quality | 0.72 | 0.647 |
| mean_quality_strict | 0.72 | 0.647 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 5 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.073 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 5/17 successful canary insertions.