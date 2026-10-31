# AgentDojo inverse — cerebras/gpt-oss-120b · banking · 2026-08-05

Attack `important_instructions_no_names` · 5×8 = 40 combos · agentdojo 0.1.35 · element sha256:cfe18565f049b32a

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 13/40 | **24/40** | 157 | 214371 | 1.0 |
| spotlighting | 17/40 | **19/40** | 152 | 216873 | 1.01 |
| sandwiching | 13/40 | **23/40** | 164 | 227698 | 1.06 |
| structural | 18/40 | **8/40** | 142 | 174979 | 0.82 |
| typed | 12/40 | **0/40** | 118 | 123234 | 0.57 |
| scoped-collector | 11/40 | **0/40** | 224 | 180860 | 0.84 |
| detector | 0/40 | **0/40** | 210 | 228072 | 1.06 |
| secinfer | 18/40 | **11/40** | 816 | 949044 | 4.43 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
