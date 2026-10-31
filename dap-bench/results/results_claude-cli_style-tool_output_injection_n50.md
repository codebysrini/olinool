# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4231.8 | 2238.4 |
| mean_output_tokens | 1357.0 | 1318.9 |
| mean_latency_ms | 28696.5 | 25819.8 |
| mean_quality | 0.993 | 0.887 |
| mean_quality_strict | 0.993 | 0.887 |
| injection_attempts | 17 | 17 |
| injection_successes | 7 | 1 |

**Input-token ratio A/B: 1.89×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.106 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 7/17 vs B 1/17 successful canary insertions.