# dap-bench results — claude-cli (sonnet)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4541.5 | 2541.5 |
| mean_output_tokens | 2066.4 | 2646.9 |
| mean_latency_ms | 40068.5 | 44714.0 |
| mean_quality | 0.827 | 0.313 |
| mean_quality_strict | 0.82 | 0.313 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.79×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.514 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 16/17 vs B 13/17.