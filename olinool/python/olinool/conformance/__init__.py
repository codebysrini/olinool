"""Shipped conformance corpus + self-certification.

The 22 language-neutral JSON vectors travel INSIDE the wheel, so any install
can prove itself:

    python -m olinool.conformance

To certify another implementation, feed it the same vectors (`iter_vectors()`)
and compare its (allowed, error) output to each vector's `expect`. Exit code 0
iff every vector matches. The same corpus certifies the TypeScript verifier —
both verifiers must produce identical verdicts on every vector.
"""
from __future__ import annotations

import json
from importlib import resources

from olinool import KeyResolver, Policy, verify_chain, verify_invocation, verify_result
from olinool.core import b64u_decode


def iter_vectors():
    """Yield (name, dict) for every shipped corpus vector, sorted by name."""
    root = resources.files(__name__) / "vectors"
    for entry in sorted(root.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".json"):
            yield entry.name, json.loads(entry.read_text())


def run_vector(v: dict) -> bool:
    resolver = KeyResolver()
    for agent_id, pub in v["keys"].items():
        resolver.register(agent_id, pub)
    pol_in = v["policy"]
    policy_kwargs = {}
    # §15 profile vectors (v09+). Presence check, NOT truthiness: an explicit
    # empty list is an explicit empty allow-list (nothing allowed — v13);
    # absent/null means the verifier default {"jws-1"}. Mirrors the TS loader
    # (corpus.test.ts), where [] is truthy — truthiness here would diverge.
    if pol_in.get("allowed_profiles") is not None:
        policy_kwargs["allowed_profiles"] = set(pol_in["allowed_profiles"])
    policy = Policy(
        min_assurance=pol_in.get("min_assurance", 0),
        trusted_principals=set(pol_in["trusted_principals"]) if pol_in.get("trusted_principals") else None,
        **policy_kwargs,
    )
    now = pol_in["now"]
    if v.get("result"):
        d = verify_result(v["result"], v["chain"][-1], resolver,
                          allowed_profiles=policy_kwargs.get("allowed_profiles"))
    elif v.get("invocation"):
        d = verify_invocation(v["chain"], v["invocation"], b64u_decode(v["request_b64"]),
                              v["receiver_id"], resolver, policy, now=now)
    else:
        d = verify_chain(v["chain"], resolver, policy, now=now)
    ok = d.allowed == v["expect"]["allowed"] and (d.error or None) == v["expect"]["error"]
    status = "PASS" if ok else f"FAIL (got allowed={d.allowed} error={d.error})"
    print(f"  {v['name']:28s} expect={v['expect']['error'] or 'ALLOW':20s} {status}")
    return ok


def certify() -> int:
    """Run every shipped vector; return 0 iff all pass (CLI exit semantics)."""
    results = [run_vector(v) for _, v in iter_vectors()]
    if not results:
        print("no vectors shipped — broken wheel")
        return 2
    print(f"\n{sum(results)}/{len(results)} vectors passed")
    return 0 if all(results) else 1
