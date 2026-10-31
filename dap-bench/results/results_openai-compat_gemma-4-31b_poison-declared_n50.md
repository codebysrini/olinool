# dap-bench results — openai-compat (gemma-4-31b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3083.1 | 1674.6 |
| mean_output_tokens | 82.2 | 84.1 |
| mean_latency_ms | 987.7 | 979.6 |
| mean_quality | 0.667 | 0.647 |
| mean_quality_strict | 0.667 | 0.647 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.020 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 0/17 vs B 0/17.