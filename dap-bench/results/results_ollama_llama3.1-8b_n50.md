# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3110.0 | 1687.8 |
| mean_output_tokens | 138.7 | 109.1 |
| mean_latency_ms | 15353.9 | 9072.7 |
| mean_quality | 0.86 | 0.72 |
| mean_quality_strict | 0.593 | 0.427 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.140 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.