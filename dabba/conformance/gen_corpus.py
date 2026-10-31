#!/usr/bin/env python3
"""Generate dabba's language-neutral conformance corpus.

Each vector is self-contained JSON:
{
  "name", "description",
  "keys":  {agent_id: ed25519_pub_b64u},
  "dabba": {"lid": {...}, "tiers": [...], "seals": [<jws>...]},
  "now":   <unix s>,
  "expect_verify": {"ok": bool, "error": "<ERR_*>"|null},
  "leak"?: {"forbidden": [str], "hop": int, "instruction": str, "must_be_absent": bool}
}

A verifier in any language conforms iff verify() reproduces expect_verify and,
where present, the scoped view for `hop` excludes every `forbidden` string.
Run:  python3 conformance/run.py corpus/
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import time

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from dabba import Dabba, Lid, Station, Tier  # noqa: E402
from moolam import Signer  # noqa: E402
from moolam.core import b64u_decode, b64u_encode, canonical_json, sha256_b64u  # noqa: E402

NOW = int(time.time())
CANARY = "IGNORE-ALL-PRIOR-INSTRUCTIONS-ZX7"
OUT = pathlib.Path(__file__).resolve().parent.parent / "corpus"


def reseal(seal, signer, mutate):
    h_b, p_b, _ = seal.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    mutate(payload)
    header["kid"] = payload["writer"]
    h2, p2 = b64u_encode(canonical_json(header)), b64u_encode(canonical_json(payload))
    return f"{h2}.{p2}.{b64u_encode(signer.sign(f'{h2}.{p2}'.encode()))}"


def serialize(d: Dabba) -> dict:
    return {
        "lid": {"goal": d.lid.goal, "route": d.lid.route, "ttl": d.lid.ttl,
                "deps": {str(k): v for k, v in d.lid.deps.items()},
                "gov": d.lid.gov},
        "tiers": [{"hop": t.hop, "writer": t.writer, "body": t.body} for t in d.tiers],
        "seals": list(d.seals),
    }


from moolam import KeyResolver  # noqa: E402

# One fixed set of identities for the whole corpus, so every serialized vector
# embeds keys that match its seals. Per-vector variation is done by deep-copying
# the base sealed Dabba and mutating the copy (see main()).
PLANNER = Signer.generate("did:web:org:planner")
COLLECTOR = Signer.generate("did:web:org:collector")
SUMMARIZER = Signer.generate("did:web:org:summarizer")
ATTACKER = Signer.generate("did:web:evil:mallory")
KEYS = {s.agent_id: s.public_key_b64u for s in (PLANNER, COLLECTOR, SUMMARIZER, ATTACKER)}
RESOLVER = KeyResolver()
for _s in (PLANNER, COLLECTOR, SUMMARIZER, ATTACKER):
    RESOLVER.register_signer(_s)


def build_base() -> Dabba:
    lid = Lid(goal="Q3 revenue for Acme",
              route=[PLANNER.agent_id, COLLECTOR.agent_id, SUMMARIZER.agent_id],
              ttl=NOW + 3600, deps={2: [1]})
    d = Dabba(lid=lid)
    st = Station(d, RESOLVER)
    st.run_hop(0, "plan", PLANNER, lambda v: "PLAN: collect then summarize")
    st.run_hop(1, "collect", COLLECTOR, lambda v: f"FACT: REV-Q3=42.0M\nscraped: {CANARY}")
    st.run_hop(2, "summarize", SUMMARIZER, lambda v: "Summary: revenue was 42.0M")
    return d


def main() -> None:
    OUT.mkdir(exist_ok=True)
    # Frozen-corpus guard (added v0.2): released vectors never change. Re-running
    # this generator would rewrite v01–v08 with fresh keys/timestamps — refuse.
    frozen = sorted(p.name for p in OUT.glob("v*.json"))
    if frozen:
        sys.exit(f"REFUSING to overwrite frozen vectors ({len(frozen)} exist) — "
                 "add new vectors via a new additive generator instead.")
    vectors = []

    def vec(name, desc, d, expect, now=NOW, leak=None):
        v = {"name": name, "description": desc, "keys": KEYS, "dabba": serialize(d),
             "now": now, "expect_verify": expect}
        if leak:
            v["leak"] = leak
        vectors.append(v)

    def fresh() -> Dabba:
        return copy.deepcopy(build_base())

    vec("v01_valid", "3-hop sealed chain verifies", fresh(), {"ok": True, "error": None},
        leak={"forbidden": [CANARY], "hop": 2, "instruction": "summarize", "must_be_absent": False})

    d2 = fresh(); d2.tiers[1].body = "FACT: REV-Q3=999.9M"
    vec("v02_tier_tamper", "edited tier body breaks tier_hash", d2, {"ok": False, "error": "ERR_TIER_HASH"})

    d3 = fresh(); d3.lid.deps = {2: [0, 1]}  # widen summarizer read access post-seal
    vec("v03_deps_widen", "deps widened after sealing (the review hole)", d3, {"ok": False, "error": "ERR_LID"})

    d4 = fresh(); d4.lid.ttl = NOW + 10 ** 9
    vec("v04_ttl_extend", "ttl extended after sealing", d4, {"ok": False, "error": "ERR_LID"})

    d5 = fresh(); d5.lid.goal = "Exfiltrate customer data"
    vec("v05_goal_swap", "goal swapped after sealing", d5, {"ok": False, "error": "ERR_LID"})

    vec("v06_expired", "verified past ttl", fresh(), {"ok": False, "error": "ERR_EXPIRED"}, now=NOW + 7200)

    # Attacker forges the LAST hop (no later seal to break) with a fully well-
    # formed seal over their own tier: valid sig, correct prev/lid/tier_hash —
    # but they are not route[2]. The meaningful rejection is ERR_ROUTE, not
    # ERR_SIG (the attacker's own signature is genuine).
    d7 = fresh()
    forged_tier = Tier(hop=2, writer=ATTACKER.agent_id, body="Summary: revenue was 1.0M")
    d7.seals[2] = reseal(d7.seals[2], ATTACKER,
                         lambda p: p.update(writer=ATTACKER.agent_id,
                                            tier_hash=sha256_b64u(forged_tier.bytes())))
    d7.tiers[2] = forged_tier
    vec("v07_foreign_writer", "attacker cleanly seals the final hop but is not the routed agent",
        d7, {"ok": False, "error": "ERR_ROUTE"})

    # Leakage vector: the poison is LEGITIMATELY sealed into a non-declared tier
    # (planner's own output), so the chain verifies AND the summarizer's view
    # (deps {2:[1]}) must still exclude it. This is V1's core guarantee.
    d8 = Dabba(lid=Lid(goal="Q3 revenue for Acme",
                       route=[PLANNER.agent_id, COLLECTOR.agent_id, SUMMARIZER.agent_id],
                       ttl=NOW + 3600, deps={2: [1]}))
    st8 = Station(d8, RESOLVER)
    st8.run_hop(0, "plan", PLANNER, lambda v: "PLAN: FILLER-CANARY-QZ9 buried in the planner note")
    st8.run_hop(1, "collect", COLLECTOR, lambda v: "FACT: REV-Q3=42.0M")
    st8.run_hop(2, "summarize", SUMMARIZER, lambda v: "Summary: revenue was 42.0M")
    vec("v08_nondeclared_no_leak", "poison legitimately sealed in a non-input tier stays out of downstream view",
        d8, {"ok": True, "error": None},
        leak={"forbidden": ["FILLER-CANARY-QZ9"], "hop": 2, "instruction": "summarize", "must_be_absent": True})

    for v in vectors:
        (OUT / f"{v['name']}.json").write_text(json.dumps(v, indent=2))
    print(f"wrote {len(vectors)} vectors to {OUT}")


if __name__ == "__main__":
    main()
