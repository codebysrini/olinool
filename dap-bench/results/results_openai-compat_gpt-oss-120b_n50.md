# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3287.1 | 1848.8 |
| mean_output_tokens | 701.8 | 633.0 |
| mean_latency_ms | 1967.1 | 2138.5 |
| mean_quality | 0.893 | 0.793 |
| mean_quality_strict | 0.86 | 0.793 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.100 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.