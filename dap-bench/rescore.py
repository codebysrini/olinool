#!/usr/bin/env python3
"""Rescore stored model outputs with the current scorer (no model re-run).

Why this exists: v2 stores every model answer precisely so scoring defects can
be fixed and applied retroactively with full provenance. Each rescored row
keeps the previous score in `quality_v2` and records `harness_version: 2.2`.
Tasks are regenerated deterministically (same seed) to recover required_facts.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bench import lenient_hit  # noqa: E402
from tasks import build_tasks  # noqa: E402

RESULTS = pathlib.Path(__file__).resolve().parent / "results"


def main(seed: int = 7, n: int = 12) -> None:
    facts = {t.tid: t.required_facts for t in build_tasks(n, seed=seed)}
    for f in sorted(RESULTS.glob("raw_*.jsonl")):
        rows = [json.loads(ln) for ln in f.read_text().splitlines() if ln.strip()]
        changed = 0
        for r in rows:
            if "final" not in r or r["task"] not in facts:
                continue
            req = facts[r["task"]]
            new_q = sum(1 for x in req if lenient_hit(x, r["final"])) / len(req)
            if new_q != r["quality"]:
                changed += 1
            r.setdefault("quality_v2", r["quality"])
            r["quality"] = new_q
            r["harness_version"] = 2.2
        f.write_text("\n".join(json.dumps(r) for r in rows))
        print(f"{f.name}: rescored, {changed} rows changed")


if __name__ == "__main__":
    main()
