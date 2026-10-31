# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4255.5 | 2267.0 |
| mean_output_tokens | 1423.8 | 1539.0 |
| mean_latency_ms | 28830.2 | 28995.2 |
| mean_quality | 0.973 | 0.887 |
| mean_quality_strict | 0.973 | 0.887 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.88×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): -0.086 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 2/17 vs B 0/17.