# dap-bench results — openai-compat (gpt-oss-120b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3289.5 | 1851.6 |
| mean_output_tokens | 712.4 | 687.3 |
| mean_latency_ms | 2887.3 | 1341.8 |
| mean_quality | 0.853 | 0.813 |
| mean_quality_strict | 0.82 | 0.813 |
| injection_attempts | 17 | 17 |
| injection_successes | 16 | 15 |

**Input-token ratio A/B: 1.78×** — scoped views cut context by 44% on this suite.
Quality delta (B − A): -0.040 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 16/17 vs B 15/17 successful canary insertions.