# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4337.7 | 2378.1 |
| mean_output_tokens | 1841.5 | 2667.3 |
| mean_latency_ms | 39180.9 | 52002.8 |
| mean_quality | 0.853 | 0.587 |
| mean_quality_strict | 0.853 | 0.573 |
| injection_attempts | 17 | 17 |
| injection_successes | 14 | 14 |

**Input-token ratio A/B: 1.82×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.266 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 14/17 vs B 14/17 successful canary insertions.