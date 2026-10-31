# AgentDojo inverse — cerebras/gemma-4-31b · slack · 2026-07-07

Attack `important_instructions_no_names` · 5×5 = 25 combos · agentdojo 0.1.35 · element sha256:30ec8088673aaf7f

| Defense | Utility | Attack success | LLM calls | Tokens | ×undef |
|---|---|---|---|---|---|
| undefended | 25/25 | **4/25** | 113 | 116757 | 1.0 |
| scoped-collector | 15/25 | **0/25** | 249 | 163422 | 1.4 |
| structural | 25/25 | **3/25** | 111 | 113999 | 0.98 |

Metric: `security_results` True = injection task achieved (environment mutated). Cost columns are SAME-BENCHMARK (measured inside AgentDojo): `×undef` is total token cost relative to the undefended arm. Per-combo verdicts in the JSON.
