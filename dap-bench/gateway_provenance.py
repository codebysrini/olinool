#!/usr/bin/env python3
"""Re-verify the serving path of a landed gateway run from its raw evidence.

Gateway runs record per-call generation ids in each record's provenance
(llm.py). The gateway's Generation Lookup API (GET /v1/generation?id=...)
returns the provider that actually served each call (provider_name) — ground
truth that outlives the run. This script tallies those upstreams for a
raw_*.jsonl and exits non-zero if any call was served outside --expect, so a
lane's serving-path claim is re-checkable by anyone holding the run's key.

Usage:
  python3 gateway_provenance.py results/raw_openai-compat_meta-llama-4-scout_n50.jsonl --expect deepinfra
  python3 gateway_provenance.py <raw.jsonl> --expect deepinfra --sample 60

Key resolution mirrors llm.py: OPENAI_COMPAT_API_KEY, else
VERCEL_AI_GATEWAY_KEY. Never hardcoded, never logged.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import random
import sys
import time
import urllib.request


def lookup(base: str, gid: str, key: str) -> str | None:
    req = urllib.request.Request(
        f"{base}/generation?id={gid}",
        headers={"authorization": f"Bearer {key}", "user-agent": "dap-bench/0.1"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read()).get("data") or {}
                return data.get("provider_name")
        except urllib.error.HTTPError as e:
            # 404 is retryable: fresh generations index with a lag of up to a
            # few minutes (observed live 2026-07-13); a still-404 id after
            # backoff counts as unverifiable (None), which fails --expect.
            if e.code not in (404, 429, 500, 502, 503) or attempt == 4:
                if e.code == 404:
                    return None
                raise
            time.sleep(min(3.0 * 2 ** attempt, 30.0))
        except (urllib.error.URLError, TimeoutError, OSError):
            # Transient network faults (read timeout, reset) retry the same
            # way; exhausted retries count as unverifiable rather than crash
            # a long verification run.
            if attempt == 4:
                return None
            time.sleep(min(3.0 * 2 ** attempt, 30.0))
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=pathlib.Path, help="raw_*.jsonl from a gateway run")
    ap.add_argument("--expect", required=True,
                    help="comma-separated provider slugs the run must have been served by")
    ap.add_argument("--sample", type=int, default=0,
                    help="verify a seeded random sample of N calls instead of all (0 = all)")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    key = os.environ.get("OPENAI_COMPAT_API_KEY") or os.environ.get("VERCEL_AI_GATEWAY_KEY")
    if not key:
        sys.exit("No key: set OPENAI_COMPAT_API_KEY or VERCEL_AI_GATEWAY_KEY.")
    expect = {s.strip() for s in args.expect.split(",") if s.strip()}

    ids: list[str] = []
    base = None
    for line in args.raw.read_text().splitlines():
        if not line.strip():
            continue
        prov = json.loads(line).get("provenance") or {}
        ids += prov.get("generation_ids") or []
        base = base or prov.get("base_url")
    if not ids:
        sys.exit(f"{args.raw.name}: no generation ids in provenance — "
                 "not a gateway run recorded after 2026-07-13, nothing to verify.")
    if not base:
        sys.exit(f"{args.raw.name}: no base_url in provenance.")

    if args.sample and args.sample < len(ids):
        ids = random.Random(args.seed).sample(ids, args.sample)

    tally: collections.Counter = collections.Counter()
    for i, gid in enumerate(ids):
        tally[lookup(base, gid, key)] += 1
        if (i + 1) % 25 == 0:
            print(f"\r{i + 1}/{len(ids)} looked up", end="", flush=True)
        time.sleep(0.05)
    print(f"\r{len(ids)}/{len(ids)} looked up")

    print(f"{args.raw.name}: upstreams = {dict(tally)}  (expect: {sorted(expect)})")
    off = {p: n for p, n in tally.items() if p not in expect}
    if off:
        sys.exit(f"FAIL — {sum(off.values())} call(s) served outside the expected set: {off}")
    print("OK — every verified call was served inside the expected set.")


if __name__ == "__main__":
    main()
