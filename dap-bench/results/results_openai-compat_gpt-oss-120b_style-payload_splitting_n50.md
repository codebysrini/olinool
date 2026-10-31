# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3291.2 | 1851.2 |
| mean_output_tokens | 706.4 | 644.1 |
| mean_latency_ms | 1432.2 | 1421.3 |
| mean_quality | 0.873 | 0.807 |
| mean_quality_strict | 0.84 | 0.807 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.066 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.