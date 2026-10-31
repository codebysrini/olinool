# AgentDojo inverse — cerebras/gpt-oss-120b · slack · 2026-07-07

Attack `system_message` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 21/25 | **19/25** | 154 | 147711 | 1.0 |
| scoped-collector | 20/25 | **0/25** | 170 | 103308 | 0.7 |
| structural | 24/25 | **17/25** | 160 | 151282 | 1.02 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
