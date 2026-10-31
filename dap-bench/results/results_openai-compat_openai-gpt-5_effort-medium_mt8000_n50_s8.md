# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3183.9 | 1736.0 |
| mean_output_tokens | 2315.1 | 2024.8 |
| mean_latency_ms | 28568.5 | 24628.0 |
| mean_quality | 1.0 | 0.927 |
| mean_quality_strict | 1.0 | 0.927 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): -0.073 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.