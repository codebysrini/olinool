#!/usr/bin/env python3
"""Run the dabba conformance corpus against the reference verifier.

    python3 conformance/run.py corpus/

Certifies any implementation: feed the same vectors, compare verify() verdict
to expect_verify and (where present) the scoped-view leakage assertion. Exit 0
iff all vectors match.
"""
from __future__ import annotations

import json
import pathlib
import sys

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from dabba import Dabba, Lid, Station, Tier, build_view  # noqa: E402
from dabba.station import audit_view_no_leak  # noqa: E402
from moolam import KeyResolver  # noqa: E402


def load(v: dict):
    resolver = KeyResolver()
    for agent_id, pub in v["keys"].items():
        resolver.register(agent_id, pub)
    ld = v["dabba"]["lid"]
    lid = Lid(goal=ld["goal"], route=ld["route"], ttl=ld["ttl"],
              gov=ld.get("gov"), deps={int(k): x for k, x in ld.get("deps", {}).items()},
              profile=ld.get("profile", "seal-1"), instructions=ld.get("instructions"))
    d = Dabba(lid=lid,
              tiers=[Tier(hop=t["hop"], writer=t["writer"], body=t["body"]) for t in v["dabba"]["tiers"]],
              seals=list(v["dabba"]["seals"]))
    return d, resolver


def run_vector(path: pathlib.Path) -> bool:
    v = json.loads(path.read_text())
    d, resolver = load(v)
    # vectors predating the profile seam carry no allow-list -> verifier default
    allowed = set(v["allowed_profiles"]) if "allowed_profiles" in v else None
    verdict = Station(d, resolver, allowed_profiles=allowed).verify(now=v["now"])
    exp = v["expect_verify"]
    ok = verdict.ok == exp["ok"] and (verdict.error or None) == exp["error"]

    leak_ok = True
    if "leak" in v:
        lk = v["leak"]
        view = build_view(d, lk["hop"], lk.get("instruction"))  # absent under seal-vh-1 (sealed Lid supplies it)
        leaked = audit_view_no_leak(view, lk["forbidden"])
        absent = leaked is None
        leak_ok = absent if lk["must_be_absent"] else True  # non-absent case is informational

    status = "PASS" if (ok and leak_ok) else f"FAIL (verify {verdict.ok}/{verdict.error}, leak_ok={leak_ok})"
    print(f"  {v['name']:26s} expect={str(exp['error'] or 'OK'):16s} {status}")
    return ok and leak_ok


def main() -> None:
    corpus = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "corpus")
    vectors = sorted(corpus.glob("*.json"))
    if not vectors:
        print(f"no vectors in {corpus}")
        sys.exit(2)
    results = [run_vector(p) for p in vectors]
    print(f"\n{sum(results)}/{len(results)} vectors passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
