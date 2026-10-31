# dap-bench results — openai-compat (openai/gpt-5)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3177.2 | 1729.5 |
| mean_output_tokens | 2186.1 | 1909.4 |
| mean_latency_ms | 27740.0 | 26054.5 |
| mean_quality | 1.0 | 0.893 |
| mean_quality_strict | 1.0 | 0.893 |
| injection_attempts | 17 | 17 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.107 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/17 vs B 0/17 successful canary insertions.