# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3110.6 | 1689.0 |
| mean_output_tokens | 144.3 | 116.9 |
| mean_latency_ms | 17014.4 | 9532.3 |
| mean_quality | 0.907 | 0.767 |
| mean_quality_strict | 0.627 | 0.42 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.140 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 17/17 vs B 12/17.