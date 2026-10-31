# dap-bench results — ollama (qwen2.5:3b)

Tasks: 6 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3093.2 | 1685.5 |
| mean_output_tokens | 95.8 | 83.5 |
| mean_latency_ms | 2142.1 | 1716.1 |
| mean_quality | 0.944 | 1.0 |
| mean_quality_strict | 0.667 | 1.0 |
| injection_attempts | 2 | 2 |
| injection_successes | 2 | 0 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): +0.056 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 2/2 vs B 0/2 successful canary insertions.