# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3110.1 | 1694.4 |
| mean_output_tokens | 109.5 | 85.4 |
| mean_latency_ms | 4707.7 | 3501.6 |
| mean_quality | 0.813 | 1.0 |
| mean_quality_strict | 0.533 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.187 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.