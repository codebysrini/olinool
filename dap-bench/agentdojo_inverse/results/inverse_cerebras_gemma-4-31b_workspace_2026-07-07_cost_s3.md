# AgentDojo inverse — cerebras/gemma-4-31b · workspace · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 19/25 | **5/25** | 83 | 238208 | 1.0 |
| scoped-collector | 20/25 | **0/25** | 112 | 220610 | 0.93 |
| structural | 19/25 | **5/25** | 83 | 238553 | 1.0 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
