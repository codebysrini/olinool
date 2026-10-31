# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4584.5 | 2534.9 |
| mean_output_tokens | 1997.9 | 3020.1 |
| mean_latency_ms | 41347.7 | 50149.8 |
| mean_quality | 0.72 | 0.267 |
| mean_quality_strict | 0.72 | 0.253 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 9 |

**Input-token ratio A/B: 1.81×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.453 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 9/17 successful canary insertions.