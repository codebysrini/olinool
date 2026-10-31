# dap-bench results — ollama (qwen2.5:3b)

Tasks: 12 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3089.4 | 1686.4 |
| mean_output_tokens | 100.3 | 88.3 |
| mean_latency_ms | 5352.9 | 3310.1 |
| mean_quality | 0.917 | 1.0 |
| mean_quality_strict | 0.75 | 1.0 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.083 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 4/4 vs B 1/4.