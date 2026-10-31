# dap-bench results — ollama (qwen2.5:7b)

Tasks: 50 per condition · pipeline: planner → collector → summarizer

| Metric | Condition A | Condition B |
|---|---|---|
| mean_input_tokens | 3086.6 | 1674.1 |
| mean_output_tokens | 92.7 | 86.9 |
| mean_latency_ms | 13519.1 | 6761.2 |
| mean_quality | 0.753 | 0.547 |
| mean_quality_strict | 0.487 | 0.467 |
| injection_attempts | 17 | 17 |
| injection_successes | 17 | 1 |

**Input-token ratio A/B: 1.84×** — scoped views cut context by 46% on this suite.
Quality delta (B − A): -0.206 (negative = scoped views lost facts; investigate before claiming speed).
Injection: A 17/17 vs B 1/17 successful canary insertions.