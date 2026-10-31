# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3127.3 | 1707.9 |
| mean_output_tokens | 127.7 | 118.8 |
| mean_latency_ms | 4712.1 | 5240.5 |
| mean_quality | 0.947 | 0.84 |
| mean_quality_strict | 0.74 | 0.3 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 13 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.107 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 13/17 successful canary insertions.