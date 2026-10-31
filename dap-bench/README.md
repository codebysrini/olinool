# dap-bench

**The benchmark that decides whether DAP gets built.** It tests exactly one hypothesis — DAP's scoped working view W(v):

> Downstream agents don't need raw upstream context. Passing each hop only its slice (Lid + instruction + minimal input) is cheaper and faster than passing full history, loses no task quality, and strips prompt-injection vectors that full history forwards.

It does NOT test routing, the Sorting Station, seal chains, or transport speed. If this benchmark fails, DAP's core premise fails and the transport should not be built. If it passes, DAP has its first TESTED claim.

## Design

Pipeline: planner → collector → summarizer (3 LLM calls per task).
Condition **A** (baseline): summarizer receives goal + planner output + all raw documents + collector output — how typical orchestrators pass context today.
Condition **B** (DAP): summarizer receives only `Lid (goal)` + collector's extraction.

Quality is deterministic: each task plants 3 ground-truth fact values in one relevant document among filler; score = fraction of values present verbatim in the final answer. No LLM judge, no judge bias, no judging cost.

Injection probe: every third task hides an instruction + canary token in an *irrelevant* document. A correct pipeline never needs that document downstream. A forwards it raw to the summarizer; B strips it. Metric: canary appears in final answer. Note the asymmetry when reading results: B's protection is **architectural** (the vector never reaches the model — model-independent), while A's number measures **model robustness** (a strong model may refuse; that's a finding about the model, not the architecture).

## Run

```bash
# free mechanics check (no key, deterministic):
python3 run.py --backend mock --n 12

# OPTION 1 — local model, free, no key (recommended; matches the project's local-first goal):
#   one-time: install Ollama from https://ollama.com, then:  ollama pull qwen2.5:3b
python3 run.py --backend ollama --n 12                # default model qwen2.5:3b

# OPTION 2 — your Claude subscription via the claude CLI, no API key:
#   one-time: npm install -g @anthropic-ai/claude-code && claude   (log in once)
python3 run.py --backend claude-cli --n 4             # default model haiku
#   caveat: latency includes CLI startup (constant across A/B) — read tokens, not ms

# OPTION 3 — Anthropic API key (console.anthropic.com), pay-per-use:
export ANTHROPIC_API_KEY=sk-ant-...                   # env only; never in code or chat
python3 run.py --backend claude --n 12                # default model claude-haiku-4-5
```

12 tasks × 2 conditions × 3 calls = 72 model calls; token totals are printed. Results land in `results/raw_<backend>.jsonl` + `results_<backend>.md`. Run at least two backends if you can — a finding that holds for both a 3B local model and Haiku is far stronger than either alone, and the local-model result doubles as evidence for the "works with local open-source models" goal.

## Mock-run status (mechanics validation only — not findings)

A/B input-token ratio 1.92× (48% context cut) on the synthetic suite; quality parity; injection 4/4 (A) vs 0/4 (B) with a deliberately gullible mock summarizer. Real numbers require the Claude run.

## Method change log (transparency)

**v2 (2026-07-02), after calibration run 1 (ollama/qwen2.5:3b, n=12), before the clean run.** Calibration exposed two harness defects: (1) v1 scoring demanded character-exact `KEY=VAL` matches and floored to ~0.03–0.08 in BOTH conditions on a 3B model — quality deltas at that floor are noise, and v1 didn't store model outputs so the failure couldn't be diagnosed post-hoc. v2 stores `final` and `collector_out` per row, adds lenient scoring (information preservation: flexible separators, distinctive values; short numerics still require the key adjacent) alongside strict, hardens the summarizer prompt, and gates on the lenient score. (2) A new gate **G0 (attainment floor)**: mean lenient quality in B must be ≥ 0.6, else the model/harness can't do the task and the whole quality comparison is declared invalid rather than "passed on a technicality." Calibration run 1's non-quality findings stand: ratio 1.87×, latency 3.3× faster in B, injection 3/4 (A) vs 0/4 (B).

**v2.2 (2026-07-02), after the clean runs.** Two instrument defects found and fixed, scores corrected from *stored* outputs (no re-run — this is why v2 stores them): (1) the lenient scorer's bare-value branch tested a regex-escaped string as a substring, so values containing `-` or `.` (ACCT-7499, 47.2M) could never match — deflating condition A specifically, since A paraphrases while B emits verbatim tokens; rescore changed 2 rows. (2) The claude CLI's json usage reports a constant ~30 input tokens for multi-KB prompts; G1 on that backend is now N/A-instrument (ratio evidence: ollama 1.86×, mock 1.91×), and the backend estimates tokens when reports are implausible. Known residual bias, disclosed: A is still under-credited when it paraphrases units ("9%" vs 9PCT), so read B's quality edge as "verbatim fact retention," not "understands better."

## Reading the outcome (decide in advance, resist rationalizing after)

Build DAP transport if: G0 attainment ≥ 0.6 in B, token ratio ≥ ~1.5×, quality delta ≥ −0.02, injection successes in B = 0.
Do not build if: quality drops materially in B (scoped views starve agents of needed context) — that kills the premise regardless of token savings.
Publishable either way: nobody has published a scoped-view vs full-history number for multi-hop agent pipelines as of the July 2026 ecosystem sweep.
