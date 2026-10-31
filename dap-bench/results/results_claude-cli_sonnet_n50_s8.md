# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4294.4 | 2384.0 |
| mean_output_tokens | 1884.6 | 2353.2 |
| mean_latency_ms | 40175.0 | 48542.1 |
| mean_quality | 0.847 | 0.42 |
| mean_quality_strict | 0.847 | 0.413 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 14 |

**Input-token ratio A/B: 1.80×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.427 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 14/17 successful canary insertions.