# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3287.0 | 1848.4 |
| mean_output_tokens | 721.3 | 620.3 |
| mean_latency_ms | 1724.2 | 1449.7 |
| mean_quality | 0.861 | 0.806 |
| mean_quality_strict | 0.833 | 0.806 |
| injection_attempts | 4 | 4 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.055 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/4 vs B 0/4 successful canary insertions.