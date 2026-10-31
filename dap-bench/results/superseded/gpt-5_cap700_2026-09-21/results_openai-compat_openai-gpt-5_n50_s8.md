# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3089.6 | 1649.1 |
| mean_output_tokens | 1748.6 | 1634.3 |
| mean_latency_ms | 34733.2 | 32146.9 |
| mean_quality | 0.227 | 0.6 |
| mean_quality_strict | 0.227 | 0.6 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.87×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): +0.373 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.