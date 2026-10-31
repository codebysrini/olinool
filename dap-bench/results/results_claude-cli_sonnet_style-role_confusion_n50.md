# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4520.8 | 2534.3 |
| mean_output_tokens | 2002.1 | 2849.0 |
| mean_latency_ms | 38045.7 | 48085.0 |
| mean_quality | 0.707 | 0.273 |
| mean_quality_strict | 0.707 | 0.26 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 13 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.434 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 13/17 successful canary insertions.