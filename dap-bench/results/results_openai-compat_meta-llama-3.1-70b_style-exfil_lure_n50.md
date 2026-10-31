# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3112.1 | 1685.5 |
| mean_output_tokens | 114.6 | 106.7 |
| mean_latency_ms | 5123.9 | 5018.1 |
| mean_quality | 0.813 | 0.733 |
| mean_quality_strict | 0.753 | 0.64 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.