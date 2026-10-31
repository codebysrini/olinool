#!/usr/bin/env python3
"""Cross-seed variance for the core-suite headline numbers.

Reads the canonical seed-7 core-suite stems (raw_<model>_n50.jsonl) plus any
variance-seed siblings (raw_<model>_n50_s<seed>.jsonl) and reports, per model
and per seed: input-token ratio A/B, quality delta (B - A), and injection
counts — then the cross-seed mean and range. compare.py deliberately excludes
_s stems from the panels; this is the one place they are aggregated, so the
paper's variance claim traces to exactly one script.

    python3 seed_variance.py            # table for all models with >=2 seeds
"""
from __future__ import annotations

import collections
import json
import pathlib
import re

RESULTS = pathlib.Path(__file__).resolve().parent / "results"


def summarize(path: pathlib.Path) -> dict | None:
    rows = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    if not ({"A", "B"} <= set(by)):
        return None
    mean = lambda rs, k: sum(r[k] for r in rs) / len(rs)
    inj = lambda rs: (sum(1 for r in rs if r.get("injection_success")),
                      sum(1 for r in rs if r.get("injected")))
    ia, ta = inj(by["A"])
    ib, tb = inj(by["B"])
    return {
        "ratio": mean(by["A"], "input_tokens") / max(mean(by["B"], "input_tokens"), 1),
        "dq": mean(by["B"], "quality") - mean(by["A"], "quality"),
        "injA": f"{ia}/{ta}", "injB": f"{ib}/{tb}",
        "injA_n": ia, "injB_n": ib,
    }


def main() -> None:
    groups: dict[str, dict[int, pathlib.Path]] = collections.defaultdict(dict)
    for f in RESULTS.glob("raw_*_n50*.jsonl"):
        stem = f.stem.replace("raw_", "")
        if any(t in stem for t in ("style-", "poison-", "seal-", "mock")):
            continue
        m = re.match(r"(.+)_n50(?:_s(\d+))?$", stem)
        if not m:
            continue
        groups[m.group(1)][int(m.group(2) or 7)] = f

    printed = 0
    for model in sorted(groups):
        seeds = groups[model]
        if len(seeds) < 2:
            continue
        printed += 1
        print(f"\n{model}  ({len(seeds)} seeds: {sorted(seeds)})")
        vals = {}
        for s in sorted(seeds):
            r = summarize(seeds[s])
            if r is None:
                print(f"  seed {s}: incomplete run — skipped")
                continue
            vals[s] = r
            print(f"  seed {s}: ratio {r['ratio']:.2f}x  dq {r['dq']:+.3f}  "
                  f"injA {r['injA']}  injB {r['injB']}")
        if len(vals) >= 2:
            rs = [v["ratio"] for v in vals.values()]
            dqs = [v["dq"] for v in vals.values()]
            ibs = [v["injB_n"] for v in vals.values()]
            print(f"  => ratio mean {sum(rs)/len(rs):.2f}x  range [{min(rs):.2f}, {max(rs):.2f}]  "
                  f"dq mean {sum(dqs)/len(dqs):+.3f}  range [{min(dqs):+.3f}, {max(dqs):+.3f}]  "
                  f"injB range [{min(ibs)}, {max(ibs)}]")
    if not printed:
        print("no model has >=2 core-suite seeds yet — seed lanes still running?")


if __name__ == "__main__":
    main()
