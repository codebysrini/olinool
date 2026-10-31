# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-07-07

Attack `system_message` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 13/25 | **6/25** | 85 | 100188 | 1.0 |
| scoped-collector | 9/25 | **0/25** | 144 | 126322 | 1.26 |
| structural | 9/25 | **3/25** | 98 | 126556 | 1.26 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
