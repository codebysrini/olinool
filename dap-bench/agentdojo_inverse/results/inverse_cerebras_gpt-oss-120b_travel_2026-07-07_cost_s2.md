# AgentDojo inverse — cerebras/gpt-oss-120b · travel · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 5/25 | **13/25** | 148 | 429676 | 1.0 |
| scoped-collector | 8/25 | **0/25** | 254 | 422667 | 0.98 |
| structural | 3/25 | **13/25** | 145 | 419735 | 0.98 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
