# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4234.0 | 2246.4 |
| mean_output_tokens | 1331.7 | 1341.9 |
| mean_latency_ms | 27788.9 | 25651.6 |
| mean_quality | 1.0 | 0.92 |
| mean_quality_strict | 1.0 | 0.907 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.88×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.