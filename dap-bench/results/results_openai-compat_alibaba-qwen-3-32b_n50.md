# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3127.5 | 1706.7 |
| mean_output_tokens | 129.6 | 113.3 |
| mean_latency_ms | 5134.1 | 4805.5 |
| mean_quality | 0.953 | 0.873 |
| mean_quality_strict | 0.78 | 0.293 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.