# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3092.4 | 1676.8 |
| mean_output_tokens | 96.3 | 88.0 |
| mean_latency_ms | 12898.3 | 7448.2 |
| mean_quality | 0.78 | 0.507 |
| mean_quality_strict | 0.567 | 0.433 |
| injection_attempts | 17 | 17 |
| injection_successes | 1 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.273 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 1/17 vs B 0/17 successful canary insertions.