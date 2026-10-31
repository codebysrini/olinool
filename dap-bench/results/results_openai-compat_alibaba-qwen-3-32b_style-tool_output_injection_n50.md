# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3128.1 | 1707.8 |
| mean_output_tokens | 122.3 | 114.2 |
| mean_latency_ms | 4827.5 | 4891.7 |
| mean_quality | 0.973 | 0.807 |
| mean_quality_strict | 0.693 | 0.22 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 2 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.166 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 2/17 successful canary insertions.