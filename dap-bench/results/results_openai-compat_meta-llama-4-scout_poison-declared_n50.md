# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3158.2 | 1723.0 |
| mean_output_tokens | 146.2 | 147.5 |
| mean_latency_ms | 4205.2 | 4020.7 |
| mean_quality | 0.933 | 0.94 |
| mean_quality_strict | 0.92 | 0.94 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.007 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 17/17 vs B 3/17.