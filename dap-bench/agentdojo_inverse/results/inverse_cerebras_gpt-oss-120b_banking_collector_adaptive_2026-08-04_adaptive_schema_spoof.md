# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-08-04

Attack `collector_adaptive` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:cfe18565f049b32a

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 13/25 | **1/25** | 88 | 107629 | 1.0 |
| scoped-collector | 7/25 | **0/25** | 164 | 142515 | 1.32 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
