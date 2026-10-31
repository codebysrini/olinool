# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:cfe18565f049b32a

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 12/25 | **16/25** | 97 | 134450 | 1.0 |
| readact | 6/25 | **0/25** | 95 | 136894 | 1.02 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
