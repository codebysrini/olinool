# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4265.7 | 2262.6 |
| mean_output_tokens | 1385.1 | 1437.0 |
| mean_latency_ms | 28402.7 | 26906.0 |
| mean_quality | 1.0 | 0.913 |
| mean_quality_strict | 1.0 | 0.9 |
| injection_attempts | 17 | 17 |
| injection_successes | 4 | 0 |

**Input-token ratio A/B: 1.89×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.087 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 4/17 vs B 0/17 successful canary insertions.