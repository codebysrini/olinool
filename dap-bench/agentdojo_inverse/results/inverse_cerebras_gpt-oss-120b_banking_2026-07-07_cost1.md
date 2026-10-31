# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 11/25 | **18/25** | 108 | 156891 | 1.0 |
| scoped-collector | 7/25 | **0/25** | 195 | 186706 | 1.19 |
| structural | 9/25 | **4/25** | 86 | 106523 | 0.68 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
