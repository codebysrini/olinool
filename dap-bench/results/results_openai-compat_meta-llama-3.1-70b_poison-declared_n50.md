# dap-bench results — openai-compat (meta/llama-3.1-70b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3111.6 | 1687.0 |
| mean_output_tokens | 116.4 | 113.9 |
| mean_latency_ms | 7389.4 | 5779.8 |
| mean_quality | 0.827 | 0.753 |
| mean_quality_strict | 0.76 | 0.66 |
| injection_attempts | 0 | 0 |
| injection_successes | 0 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.074 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 0/0 vs B 0/0 successful canary insertions.
Declared-dependency poisoning (T4, V1's honest boundary — scoping does not block this class by design): A 17/17 vs B 9/17.