# dap-bench results — openai-compat (alibaba/qwen-3-32b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3131.8 | 1711.6 |
| mean_output_tokens | 129.0 | 122.0 |
| mean_latency_ms | 5304.4 | 4993.4 |
| mean_quality | 0.947 | 0.927 |
| mean_quality_strict | 0.62 | 0.467 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.020 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 17/17 vs B 17/17.