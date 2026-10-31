# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4552.6 | 2510.2 |
| mean_output_tokens | 1985.0 | 2544.6 |
| mean_latency_ms | 39585.5 | 44600.2 |
| mean_quality | 0.787 | 0.307 |
| mean_quality_strict | 0.787 | 0.293 |
| injection_attempts | 17 | 17 |
| injection_successes | 1 | 4 |

**Input-token ratio A/B: 1.81×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.480 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 1/17 vs B 4/17 successful canary insertions.