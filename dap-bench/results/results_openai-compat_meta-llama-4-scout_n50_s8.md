# dap-bench results — openai-compat (meta/llama-4-scout)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3148.9 | 1714.6 |
| mean_output_tokens | 129.7 | 132.2 |
| mean_latency_ms | 4440.8 | 4736.3 |
| mean_quality | 0.82 | 0.88 |
| mean_quality_strict | 0.82 | 0.867 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 14 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.060 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 14/17 successful canary insertions.