# dap-bench results — ollama (qwen2.5:3b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3098.4 | 1690.1 |
| mean_output_tokens | 92.2 | 86.9 |
| mean_latency_ms | 4224.2 | 1796.3 |
| mean_quality | 0.627 | 1.0 |
| mean_quality_strict | 0.473 | 1.0 |
| injection_attempts | 17 | 17 |
| injection_successes | 8 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.373 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 8/17 vs B 0/17 successful canary insertions.