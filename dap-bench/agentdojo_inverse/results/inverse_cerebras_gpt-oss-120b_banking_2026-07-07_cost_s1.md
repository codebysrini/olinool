# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 11/25 | **20/25** | 111 | 158237 | 1.0 |
| scoped-collector | 7/25 | **0/25** | 198 | 185814 | 1.17 |
| structural | 10/25 | **4/25** | 93 | 120687 | 0.76 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
