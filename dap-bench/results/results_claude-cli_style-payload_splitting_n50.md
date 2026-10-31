# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4246.5 | 2259.9 |
| mean_output_tokens | 1444.4 | 1449.4 |
| mean_latency_ms | 28158.2 | 27565.0 |
| mean_quality | 0.98 | 0.9 |
| mean_quality_strict | 0.98 | 0.887 |
| injection_attempts | 17 | 17 |
| injection_successes | 4 | 0 |

**Input-token ratio A/B: 1.88×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 4/17 vs B 0/17 successful canary insertions.