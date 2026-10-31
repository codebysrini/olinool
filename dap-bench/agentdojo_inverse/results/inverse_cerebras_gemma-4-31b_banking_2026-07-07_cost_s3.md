# AgentDojo inverse — cerebras/gemma-4-31b · banking · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 20/25 | **21/25** | 105 | 141517 | 1.0 |
| scoped-collector | 13/25 | **0/25** | 250 | 206706 | 1.46 |
| structural | 20/25 | **6/25** | 97 | 121586 | 0.86 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
