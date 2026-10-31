# AgentDojo inverse — scoped-views as a defense, scored on AgentDojo's metric

Reference code + committed evidence for the INVERSE evaluation described in
`../AGENTDOJO_INVERSE_DESIGN.md`. Scoped-view delivery (dabba's discipline) is
run as an AgentDojo pipeline element and scored on AgentDojo's OWN env-mutation
metric (`security_results` True = the injection task was achieved).

**Provenance rule:** every number in the design doc / paper must trace to a file
in `results/` here — never to scratch output. `run_inverse.py` emits both a
machine-readable `.json` (per-combo verdicts + full metadata: model, provider,
date, agentdojo version, attack, suite, element hash) and a `.md` summary.

## Files
- `scoped_view.py` — two defenses. `ScopedCollector` (LLM collector, an element
  after `ToolsExecutor()`) — validated, evidence in `results/`. `StructuralScope`
  (deterministic no-LLM field projection, used as `ToolsExecutor`'s
  `tool_output_formatter`) — validated 2026-07-06 by the full matrix
  (`results/inverse_cerebras_*_matrix.json`; per-suite schemas in `run_inverse.py`
  `SUITE_SCHEMAS` and recorded in each file's meta). See DESIGN §5b for the
  matrix, §7 for the PRE-REGISTERED partial-defense boundary it confirmed.
- `run_inverse.py` — runner; `INV_DEFENSES=undefended,scoped-collector,structural`
  (comma list); `INV_TAG` suffixes the output slug; an overwrite guard refuses to
  touch an existing evidence file BEFORE any spend. Writes JSON + MD to `results/`.
- `check_structural.py` — offline deterministic checks for `StructuralScope`
  (no model, no network). Not named `test_*` so dap-bench pytest never collects it.
- `results/` — the evidence of record (JSON + MD per run). Do not hand-edit.

## Reproduce
AgentDojo is not a dap-bench dependency; use a separate py3.12 venv (heavy deps):
```
python3.12 -m venv .venv-adojo && .venv-adojo/bin/pip install agentdojo
```
Then (a provider key must be in the environment; never hardcode it):
```
cd dap-bench/agentdojo_inverse
INV_PROVIDER=cerebras INV_MODEL=gpt-oss-120b INV_SUITE=slack \
INV_ATTACK=important_instructions_no_names INV_NUSER=5 INV_NINJ=5 \
  <venv>/bin/python run_inverse.py
```
Providers: `cerebras` / `groq` (metered or free cloud, Cloudflare-fronted, UA
header set) · `ollama` (local, keyless). `INV_DEFENSES` defaults to
`undefended,scoped-collector`.

## Metric direction (do not misread)
`security_results[(user_task, injection_task)] == True` means the **attacker's**
injection task succeeded (environment mutated) — the same `_check_task_result`
AgentDojo uses to score the user task's utility. Lower attack-success = better
defense. This was verified from source, not assumed.
