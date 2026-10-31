# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3285.1 | 1848.5 |
| mean_output_tokens | 662.9 | 657.6 |
| mean_latency_ms | 1469.6 | 1316.8 |
| mean_quality | 0.873 | 0.82 |
| mean_quality_strict | 0.84 | 0.82 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 0 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.053 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 0/17 successful canary insertions.