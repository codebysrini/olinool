# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3136.6 | 1707.9 |
| mean_output_tokens | 126.8 | 109.8 |
| mean_latency_ms | 4346.6 | 3702.0 |
| mean_quality | 0.887 | 0.76 |
| mean_quality_strict | 0.38 | 0.193 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 3 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.127 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 3/17 successful canary insertions.