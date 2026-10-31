# SUPERSEDED — first gpt-5 lane (2026-09-21), not evidence

`openai/gpt-5` via the Vercel gateway (pinned `openai`), core suite, n=50, seeds 7/8/9, run under the
harness's default 700-token per-hop output cap. gpt-5 is a reasoning model: its hidden reasoning counts
against that cap, so most answers came back EMPTY (condition-A finals empty on 33–35/50 tasks, 13–16 of 17
injected), and the scorer counted them as "injection resisted" (Inj. A 0/17) and as quality 0 (Δq +.36 to
+.40). The harness's old guard caught only total failure, so the lane landed.

Superseded by `../../raw_openai-compat_openai-gpt-5_effort-medium_mt8000_n50{,_s8,_s9}.jsonl` (same model,
same default reasoning effort, per-hop cap 8000; harness commit 5db504e, which records every call's
finish_reason and refuses runs with an empty or truncated hop). Kept here, outside every evidence glob, as
disclosed diagnostics. Byte-identical to the files first written to `results/`.
