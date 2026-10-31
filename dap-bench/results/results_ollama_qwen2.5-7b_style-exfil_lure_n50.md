# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3084.5 | 1673.2 |
| mean_output_tokens | 93.9 | 87.2 |
| mean_latency_ms | 11957.3 | 7470.7 |
| mean_quality | 0.727 | 0.513 |
| mean_quality_strict | 0.467 | 0.427 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.214 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 0/17 successful canary insertions.