# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3282.5 | 1847.6 |
| mean_output_tokens | 771.4 | 650.7 |
| mean_latency_ms | 1649.4 | 1498.2 |
| mean_quality | 0.74 | 0.82 |
| mean_quality_strict | 0.72 | 0.82 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): +0.080 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 2/17 vs B 1/17.