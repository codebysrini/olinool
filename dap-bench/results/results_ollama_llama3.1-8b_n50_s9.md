# dap-bench results — ollama (llama3.1:8b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3110.6 | 1687.8 |
| mean_output_tokens | 140.5 | 110.2 |
| mean_latency_ms | 28755.8 | 10850.0 |
| mean_quality | 0.867 | 0.76 |
| mean_quality_strict | 0.627 | 0.447 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.107 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.