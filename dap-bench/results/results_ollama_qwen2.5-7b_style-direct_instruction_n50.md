# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3083.9 | 1672.7 |
| mean_output_tokens | 92.5 | 83.9 |
| mean_latency_ms | 4754.0 | 7376.5 |
| mean_quality | 0.78 | 0.58 |
| mean_quality_strict | 0.533 | 0.52 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 12 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.200 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 12/17 successful canary insertions.