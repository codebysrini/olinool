# dap-bench results — claude-cli (haiku)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 4232.3 | 2215.2 |
| mean_output_tokens | 1334.4 | 1360.7 |
| mean_latency_ms | 27146.7 | 26764.4 |
| mean_quality | 0.973 | 0.967 |
| mean_quality_strict | 0.973 | 0.96 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 2 |

**Input-token ratio A/B: 1.91×** — scoped views cut context by 48% on this suite.
Quality delta (B − A): -0.006 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 2/17 successful canary insertions.