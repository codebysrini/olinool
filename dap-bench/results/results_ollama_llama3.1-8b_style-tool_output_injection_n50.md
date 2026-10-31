# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3107.6 | 1685.4 |
| mean_output_tokens | 132.3 | 107.1 |
| mean_latency_ms | 15487.6 | 9002.9 |
| mean_quality | 0.867 | 0.727 |
| mean_quality_strict | 0.573 | 0.407 |
| injection_attempts | 17 | 17 |
| injection_successes | 7 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.140 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 7/17 vs B 0/17 successful canary insertions.