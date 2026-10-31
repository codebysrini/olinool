# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3083.5 | 1673.7 |
| mean_output_tokens | 88.1 | 86.4 |
| mean_latency_ms | 12756.1 | 7675.8 |
| mean_quality | 0.8 | 0.62 |
| mean_quality_strict | 0.66 | 0.56 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.180 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 17/17 vs B 11/17.