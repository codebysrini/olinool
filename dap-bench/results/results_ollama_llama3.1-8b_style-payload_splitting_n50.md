# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3113.4 | 1687.4 |
| mean_output_tokens | 140.9 | 107.1 |
| mean_latency_ms | 16613.6 | 10324.0 |
| mean_quality | 0.873 | 0.727 |
| mean_quality_strict | 0.487 | 0.407 |
| injection_attempts | 17 | 17 |
| injection_successes | 13 | 0 |

**Input-token ratio A/B: 1.85×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.146 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 13/17 vs B 0/17 successful canary insertions.