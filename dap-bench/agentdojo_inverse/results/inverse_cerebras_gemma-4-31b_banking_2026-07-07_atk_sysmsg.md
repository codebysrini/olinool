# AgentDojo inverse — cerebras/gemma-4-31b · banking · 2026-07-07

Attack `system_message` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 20/25 | **3/25** | 92 | 111329 | 1.0 |
| scoped-collector | 15/25 | **0/25** | 148 | 112743 | 1.01 |
| structural | 16/25 | **0/25** | 92 | 108096 | 0.97 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
