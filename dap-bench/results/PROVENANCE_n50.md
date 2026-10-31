# n=50 scale program — evidence provenance

The `_n50` stem records backend + model but NOT the serving `base_url`, and some
model slugs (e.g. `gpt-oss-120b`) are hosted by multiple providers. This manifest
is the authoritative serving-path record for the replication table. One row per
provider/model lane. Maintained by the scale-run coordinator; dated 2026-07-06,
gateway-lane v2 update 2026-07-13.

| Stem prefix | backend | base_url (serving path) | upstream | model(s) | tier |
|---|---|---|---|---|---|
| `raw_ollama_qwen2.5-3b_*_n50` | ollama | local `http://localhost:11434` | n/a (local) | qwen2.5:3b | local |
| `raw_ollama_qwen2.5-7b_*_n50` | ollama | local `http://localhost:11434` | n/a (local) | qwen2.5:7b | local |
| `raw_ollama_llama3.1-8b_*_n50` | ollama | local `http://localhost:11434` | n/a (local) | llama3.1:8b | local |
| `raw_openai-compat_gpt-oss-120b_*_n50` | openai-compat | `https://api.cerebras.ai/v1` | Cerebras (wafer-scale, first-party) | gpt-oss-120b | Cerebras **paid** |
| `raw_openai-compat_gemma-4-31b_*_n50` | openai-compat | `https://api.cerebras.ai/v1` | Cerebras (wafer-scale, first-party) | gemma-4-31b | Cerebras **paid** |
| `raw_claude-cli_*_n50` (no model suffix) | claude-cli | local `claude` CLI | Anthropic (Max plan) | haiku | Max plan |
| `raw_claude-cli_sonnet_*_n50` | claude-cli | local `claude` CLI | Anthropic (Max plan) | sonnet | Max plan |
| `raw_openai-compat_meta-llama-3.1-70b_*_n50` | openai-compat | `https://ai-gateway.vercel.sh/v1` | **DeepInfra, pinned** (`--gateway-only deepinfra`; per-record generation ids, verified via `gateway_provenance.py`) | meta/llama-3.1-70b | Vercel **paid** |
| `raw_openai-compat_meta-llama-4-scout_*_n50` | openai-compat | `https://ai-gateway.vercel.sh/v1` | **DeepInfra, pinned** (`--gateway-only deepinfra`; per-record generation ids, verified via `gateway_provenance.py`) | meta/llama-4-scout | Vercel **paid** |
| `raw_openai-compat_alibaba-qwen-3-32b_*_n50` | openai-compat | `https://ai-gateway.vercel.sh/v1` | **Alibaba first-party** (routing.resolvedProvider=alibaba) | alibaba/qwen-3-32b | Vercel **paid** ($10) |

## Notes

- **Cerebras `gpt-oss-120b` is provenance-distinct** from the same model slug on
  Groq or the Vercel gateway — this manifest is the only record of that. If a
  Groq/gateway `gpt-oss-120b` file is ever added, it MUST carry a disambiguating
  stem or its own manifest row.
- **Program status (2026-07-07): all four lanes COMPLETE at n=50, 8 suites each**
  — ollama (3 models, 24/24), Vercel gateway (3 models, 24/24), claude-cli haiku
  (8/8) and claude-cli sonnet (8/8). Architecture verdict stays frozen on the n=12
  reference (Panel (i), BUILD); these rows feed only the never-gating economics and
  model-robustness panels of `comparison.md`.
- **Vercel AI Gateway lane — v2 (2026-07-13): llama-3.1-70b / llama-4-scout,
  upstream PINNED to DeepInfra.** The two meta-model lanes were re-run at n=50,
  8 suites each, with `--gateway-only deepinfra` (run.py/llm.py, landed
  2026-07-13): the gateway errors on a provider mismatch instead of rerouting,
  so the serving path is fixed for the whole lane. Verified live 2026-07-13
  that the gateway's compat responses **no longer inline
  `provider_metadata.gateway.routing`** (the v1 mechanism); each v2 record
  instead carries per-call `generation_ids` plus the pinned set, and
  `gateway_provenance.py` re-verifies the true upstream per call against the
  gateway's Generation Lookup API (`provider_name`). Every scout call and every
  llama-3.1-70b call verified `deepinfra`. The 70B row is **meta/llama-3.1-70b**
  in v2: DeepInfra does not serve llama-3.3-70b, so the pinned 70B-class lane
  uses the 3.1 release. The v1 lane files (scout and llama-3.3-70b, upstream
  resolved per run rather than pinned) and the retired n=12-era Groq files were
  moved out of the repo 2026-07-13; superseded evidence is retained privately.
  qwen-3-32b is unchanged from v1: "qwen-3-32b (Alibaba via Vercel AI Gateway;
  upstream resolved per run)". Replication rows for the v2 lanes read
  "(DeepInfra via Vercel AI Gateway; upstream pinned per run, verified per
  record)". The model slug alone does not name the true serving path.
- **claude-cli token meter is N/A-instrument (haiku AND sonnet).** The claude CLI
  does not return token usage, so `input_tokens`/`output_tokens` are estimated and
  UNRELIABLE for both claude-cli rows. These rows are valid for **quality and
  injection-count evidence ONLY** — EXCLUDE them from any A/B token-ratio /
  economics claim. compare.py auto-flags mean-A < 200 tokens; this manifest is the
  second, explicit guard so the exclusion does not rely on that flag alone.
- **Provenance boundary — DATED DECISION (Srini, 2026-07-07):**
  - **Runs on/before 2026-07-07 (this n=50 program):** provenance is **per-run via
    this manifest**, authoritative. `llm.py` is NOT modified mid-run (that would
    split the V-lane record schema — worse than a uniform manifest) and the
    affected suites are NOT re-run (no marginal spend). The per-request-failover
    gap the manifest can't catch was NOT observed in probing and is handled by
    disclosure, not spend: rows state "upstream resolved per run" (above).
  - **Runs AFTER 2026-07-07 (later re-runs, multi-seed):** an
    `llm.py` change stores `base_url` + `provider_metadata.gateway.routing.
    resolvedProvider` into each record, closing the gap permanently at zero
    marginal cost (those runs haven't started). **Status: LANDED 2026-07-07**,
    after the n=50 gateway (V) lane closed 24/24 — so no openai-compat run was in
    flight to schema-split. `OpenAICompatLLM` sets a per-call `provenance`
    (base_url + resolved upstream); the record builders (`bench.py`,
    `bench_dabba.py`) add a `provenance` key ONLY when a call carried it, folding
    the distinct upstreams seen across a task's hops in order (a >1-element
    `resolved_provider` list = per-request failover WITHIN one task — the exact
    case this manifest could not capture). Deliberately a **no-op for
    mock/ollama/claude-cli records** (they stay byte-identical), which is why it
    could land safely while the claude-cli sonnet lane was still running: those
    records never gain the key, so that lane cannot split. This dated boundary
    makes the manifest-vs-record provenance transition itself auditable.
- **Groq lane: retired**, superseded by the gateway lane. The n=12-era Groq
  files (`llama-3.3-70b-versatile`, `meta-llama-llama-4-scout-17b-16e-instruct`,
  `openai-gpt-oss-120b`, no `_n50` suffix) were moved out of the repo
  2026-07-13 so `compare.py`'s glob no longer ingests retired rows; they fed no
  paper claim.

## Addendum 2026-08-04 — variance seeds (core suite, seeds 8/9)

Every model in the replication table now carries THREE core-suite seeds
(canonical 7 + variance 8/9) on `_s8`/`_s9` stems; `seed_variance.py` is the
single aggregation point (panels remain canonical-seed by compare.py's
exclusion). Serving paths identical to the canonical lanes: local ollama;
Cerebras first-party; gateway pinned `deepinfra` (llama-4-scout,
llama-3.1-70b) and pinned `alibaba` (qwen-3-32b), spot-verified per call via
generation lookup. Alibaba API change noted 2026-08-04: non-streaming calls
now require `providerOptions.alibaba.enableThinking=false` (run.py
`--provider-options`); behaviorally identical to the July canonical lane,
which predated the requirement. Cross-seed snapshot:
`SEED_VARIANCE_2026-08-04.txt`.

## Addendum 2026-09-22 — gpt-5 lane (frontier, closed) and the Claude CLI lanes

| Stem prefix | backend | base_url (serving path) | upstream | model | tier |
|---|---|---|---|---|---|
| `raw_openai-compat_openai-gpt-5_effort-medium_mt8000_*_n50` | openai-compat | `https://ai-gateway.vercel.sh/v1` | **OpenAI first-party, pinned** (`--gateway-only openai`; 900/900 calls verified `openai` via `gateway_provenance.py`) | openai/gpt-5 | Vercel **paid** |

Configuration (from each run's `manifest_*.json`, harness commit `5db504e`): reasoning effort `medium`
(gpt-5's default) via `--provider-options`, per-hop output cap `--max-tokens 8000` (hidden reasoning
counts against it: mean 601, max 1,536 tokens per call), dabba runtime, seeds 7/8/9. gpt-5 exposes no
temperature control: the harness still sends `temperature: 0`, which the model ignores, so this lane is
sampled at gpt-5's fixed default and its seeds include sampling variance. Every record carries per-hop
`finish_reasons` (all `stop`) and `reasoning_tokens`.

- **Superseded first lane** (700-token cap; most answers truncated to empty) is kept, outside the
  evidence glob, in `superseded/gpt-5_cap700_2026-09-21/` with its own README.
- **One refused attempt**: seed 8's first re-run was refused by the validity guard for a single empty
  collector output (t027/B, `finish_reason=stop` on every hop, i.e. the model's own choice, not
  truncation); kept in `invalid/…_s8_attempt1.*`. Seed 8 was re-run and passed every gate.
- **Claude CLI lanes** (`raw_claude-cli_*`): the CLI records only the requested alias. The served Sonnet
  version, recovered from the CLI's own session records, is `claude-sonnet-5` for the seed-8/9 lanes
  (2026-08-05); the seed-7 lane (2026-07-07) ran under the same `sonnet` alias, but its session record did
  not survive. The Haiku lanes' served version was not recorded. The CLI also carries the pipeline's
  system prompt inside the user message, under Claude Code's own system prompt (a harness difference
  from every API lane).
