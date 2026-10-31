# AgentDojo inverse — cerebras/gpt-oss-120b · workspace · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 14/25 | **9/25** | 87 | 206368 | 1.0 |
| scoped-collector | 16/25 | **0/25** | 179 | 309890 | 1.5 |
| structural | 14/25 | **9/25** | 91 | 215760 | 1.05 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
