# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3139.0 | 1708.9 |
| mean_output_tokens | 130.9 | 112.5 |
| mean_latency_ms | 4134.0 | 3902.1 |
| mean_quality | 0.893 | 0.76 |
| mean_quality_strict | 0.553 | 0.12 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 6 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.133 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 6/17 successful canary insertions.