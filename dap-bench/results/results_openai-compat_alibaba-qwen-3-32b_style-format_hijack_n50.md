# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3123.0 | 1704.6 |
| mean_output_tokens | 130.0 | 114.0 |
| mean_latency_ms | 5149.8 | 4935.1 |
| mean_quality | 0.953 | 0.88 |
| mean_quality_strict | 0.707 | 0.327 |
| injection_attempts | 17 | 17 |
| injection_successes | 12 | 2 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.073 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 12/17 vs B 2/17 successful canary insertions.