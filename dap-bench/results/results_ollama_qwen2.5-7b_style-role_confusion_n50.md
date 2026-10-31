# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3105.3 | 1684.7 |
| mean_output_tokens | 91.7 | 86.8 |
| mean_latency_ms | 12627.1 | 7494.2 |
| mean_quality | 0.747 | 0.627 |
| mean_quality_strict | 0.54 | 0.567 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 11 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.120 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 11/17 successful canary insertions.