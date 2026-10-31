# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3133.5 | 1710.1 |
| mean_output_tokens | 121.8 | 114.8 |
| mean_latency_ms | 5337.5 | 6242.2 |
| mean_quality | 0.94 | 0.853 |
| mean_quality_strict | 0.68 | 0.307 |
| injection_attempts | 17 | 17 |
| injection_successes | 1 | 1 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.087 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 1/17 vs B 1/17 successful canary insertions.