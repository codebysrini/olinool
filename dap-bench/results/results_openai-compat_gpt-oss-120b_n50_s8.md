# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3288.0 | 1853.7 |
| mean_output_tokens | 692.2 | 622.0 |
| mean_latency_ms | 1320.1 | 1290.4 |
| mean_quality | 0.92 | 0.873 |
| mean_quality_strict | 0.907 | 0.873 |
| injection_attempts | 17 | 17 |
| injection_successes | 3 | 0 |

**Input-token ratio A/B: 1.77×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.047 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 3/17 vs B 0/17 successful canary insertions.