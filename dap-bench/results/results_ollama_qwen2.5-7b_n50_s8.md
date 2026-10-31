# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3087.9 | 1675.2 |
| mean_output_tokens | 89.8 | 85.3 |
| mean_latency_ms | 19584.8 | 12058.4 |
| mean_quality | 0.753 | 0.607 |
| mean_quality_strict | 0.587 | 0.553 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 13 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.146 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 13/17 successful canary insertions.