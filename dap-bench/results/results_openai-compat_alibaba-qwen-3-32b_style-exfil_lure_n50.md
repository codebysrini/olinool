# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3126.3 | 1704.6 |
| mean_output_tokens | 124.5 | 112.1 |
| mean_latency_ms | 5015.0 | 4570.8 |
| mean_quality | 0.96 | 0.867 |
| mean_quality_strict | 0.727 | 0.273 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.093 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.