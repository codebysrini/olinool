# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3177.0 | 1737.3 |
| mean_output_tokens | 144.8 | 155.1 |
| mean_latency_ms | 4383.1 | 4486.2 |
| mean_quality | 0.907 | 0.94 |
| mean_quality_strict | 0.9 | 0.927 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 16 |

**Input-token ratio A/B: 1.83×** — scoped views cut context by 45% on this suite.
Quality delta (B − A): +0.033 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 16/17 successful canary insertions.