# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3148.5 | 1716.7 |
| mean_output_tokens | 125.2 | 117.9 |
| mean_latency_ms | 4762.8 | 4945.0 |
| mean_quality | 0.947 | 0.847 |
| mean_quality_strict | 0.74 | 0.333 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 15 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.100 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 15/17 successful canary insertions.