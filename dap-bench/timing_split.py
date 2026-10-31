#!/usr/bin/env python3
"""TTFT/TPS split from server-side timing (hop_timing records, ollama lanes).

Convention in LLM serving reports is to split responsiveness (time to first
token) from throughput (tokens/second) instead of one end-to-end mean. Our
scoping intervention only shrinks PROMPTS, so the honest expectation is:
prompt-processing time drops where views shrink (the scoped summarizer hop),
decode throughput stays flat. This script computes exactly that from the
server-reported durations (Ollama measures them itself — no client jitter):

  TTFT proxy (per hop)  = load_duration + prompt_eval_duration
  decode TPS (per hop)  = eval_count / eval_duration

    python3 timing_split.py results/raw_ollama_qwen2.5-3b_n50_s10.jsonl
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

HOPS = ("planner", "collector", "summarizer")


def main() -> None:
    path = pathlib.Path(sys.argv[1])
    rows = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    rows = [r for r in rows if r.get("hop_timing")]
    if not rows:
        sys.exit(f"{path.name}: no hop_timing records — run with the timing-capturing "
                 "ollama backend (landed 2026-08-04).")

    agg: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        for hop, tm in r["hop_timing"].items():
            a = agg[(r["condition"], hop)]
            a["ttft"].append(tm.get("load_duration", 0) + tm.get("prompt_eval_duration", 0))
            if tm.get("eval_duration"):
                a["tps"].append(tm.get("eval_count", 0) / (tm["eval_duration"] / 1000.0))
            a["decode"].append(tm.get("eval_duration", 0))

    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0
    print(f"{path.name} — {len(rows)} timing records\n")
    print(f"{'cond':4s} {'hop':10s} {'TTFT-proxy ms':>14s} {'decode ms':>10s} {'TPS':>7s}")
    for cond in sorted({c for c, _ in agg}):
        for hop in HOPS:
            a = agg.get((cond, hop))
            if not a:
                continue
            print(f"{cond:4s} {hop:10s} {mean(a['ttft']):14.0f} {mean(a['decode']):10.0f} "
                  f"{mean(a['tps']):7.1f}")
        tot_ttft = sum(mean(agg[(cond, h)]["ttft"]) for h in HOPS if (cond, h) in agg)
        tot_dec = sum(mean(agg[(cond, h)]["decode"]) for h in HOPS if (cond, h) in agg)
        print(f"{cond:4s} {'TOTAL':10s} {tot_ttft:14.0f} {tot_dec:10.0f}\n")

    # A/B ratios on the split — the paper's numbers
    def tot(cond, key):
        return sum(mean(agg[(cond, h)][key]) for h in HOPS if (cond, h) in agg)
    if tot("B", "ttft"):
        print(f"prompt-processing (TTFT-proxy) ratio A/B: {tot('A','ttft')/tot('B','ttft'):.2f}x")
    if tot("B", "decode"):
        print(f"decode-time ratio A/B:                    {tot('A','decode')/tot('B','decode'):.2f}x")
    sA = [x for h in HOPS for x in agg.get(("A", h), {}).get("tps", [])]
    sB = [x for h in HOPS for x in agg.get(("B", h), {}).get("tps", [])]
    if sA and sB:
        print(f"decode TPS A vs B (flat expected):        {mean(sA):.1f} vs {mean(sB):.1f} tok/s")
    # the scoped hop specifically
    a, b = agg.get(("A", "summarizer")), agg.get(("B", "summarizer"))
    if a and b and mean(b["ttft"]):
        print(f"summarizer-hop TTFT-proxy ratio A/B:      {mean(a['ttft'])/mean(b['ttft']):.2f}x")


if __name__ == "__main__":
    main()
