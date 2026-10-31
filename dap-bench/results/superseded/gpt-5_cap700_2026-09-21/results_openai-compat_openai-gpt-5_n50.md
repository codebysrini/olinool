# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3107.2 | 1653.4 |
| mean_output_tokens | 1752.9 | 1607.4 |
| mean_latency_ms | 24737.3 | 22186.5 |
| mean_quality | 0.28 | 0.68 |
| mean_quality_strict | 0.28 | 0.68 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.88×** — scoped views cut context by 47% on this suite.
Quality delta (B − A): +0.400 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.