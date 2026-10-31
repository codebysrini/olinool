#!/usr/bin/env python3
"""Generate the language-neutral conformance corpus.

Each vector is a self-contained JSON file:
{
  "name": "...", "description": "...",
  "keys":       {agent_id: ed25519_public_key_b64u},
  "chain":      [<receipt JWS>, ...],
  "invocation": <invocation JWS> | null,
  "request_b64": "<b64u request bytes>" | null,
  "receiver_id": "...",
  "policy":     {"now": <unix s>, "min_assurance": 0, "trusted_principals": [...] | null},
  "expect":     {"allowed": bool, "error": "<ERR_*>" | null}
}
A verifier in ANY language passes conformance iff it returns exactly
`expect` for every vector. Run against the reference impl:
    python3 conformance/run.py corpus/
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from olinool import Signer, attenuate, invoke, mint_result, mint_root  # noqa: E402
from olinool.core import b64u_decode, b64u_encode, canonical_json  # noqa: E402

NOW = int(time.time())
RECEIVER = "did:web:data.example"
REQ = b'{"method":"GET","path":"/datasets/eu-42"}'
OUT = pathlib.Path(__file__).resolve().parent.parent / "python" / "olinool" / "conformance" / "vectors"


def resign(jws: str, signer: Signer, mutate) -> str:
    h_b, p_b, _ = jws.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    mutate(payload)
    header["kid"] = payload["iss"]
    h2 = b64u_encode(canonical_json(header))
    p2 = b64u_encode(canonical_json(payload))
    return f"{h2}.{p2}.{b64u_encode(signer.sign(f'{h2}.{p2}'.encode()))}"


def main() -> None:
    principal = Signer.generate("did:web:acme.example")
    orch = Signer.generate("did:web:acme.example:orchestrator")
    research = Signer.generate("did:web:acme.example:researcher")
    collect = Signer.generate("did:web:vendor.example:collector")
    summar = Signer.generate("did:web:vendor.example:summarizer")
    attacker = Signer.generate("did:web:evil.example:mallory")
    signers = [principal, orch, research, collect, summar, attacker]
    keys = {s.agent_id: s.public_key_b64u for s in signers}

    r0 = mint_root(principal, orch.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 50}},
                          {"act": "write", "res": "reports/*"}],
                   ttl_s=3600, max_depth=4, now=NOW)
    r1 = attenuate(r0, orch, research.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 25}}], now=NOW)
    r2 = attenuate(r1, research, collect.agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-*", "limits": {"amount": 10}}], now=NOW)
    r3 = attenuate(r2, collect, summar.agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
                   audience=[RECEIVER], now=NOW)
    chain = [r0, r1, r2, r3]
    inv_ok = invoke(chain[-1], summar, RECEIVER, REQ, now=NOW, nonce="vec-nonce-1")

    def vec(name, description, chain_, invocation, expect, policy_extra=None, result=None):
        v = dict(
            name=name, description=description, keys=keys, chain=chain_,
            invocation=invocation, request_b64=b64u_encode(REQ), receiver_id=RECEIVER,
            policy={"now": NOW, "min_assurance": 0, "trusted_principals": None, **(policy_extra or {})},
            expect=expect,
        )
        if result is not None:  # only result vectors carry the key (r01+, v0.2)
            v["result"] = result
        return v

    widened = resign(r3, collect, lambda p: p.update(
        scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 500}}]))
    rogue = resign(r3, attacker, lambda p: p.update(iss=attacker.agent_id))
    alt_r2 = attenuate(r1, research, collect.agent_id,
                       scope=[{"act": "read", "res": "datasets/eu-*", "limits": {"amount": 10}}], now=NOW)
    inv_stolen = invoke(chain[-1], attacker, RECEIVER, REQ, now=NOW, nonce="vec-nonce-2")

    # Result-record vectors (v0.2, spec §14). Verified against chain[-1] as leaf.
    OUTPUT = b"Summary: revenue was 42.0M"
    alt_r3 = attenuate(alt_r2, collect, summar.agent_id,
                       scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
                       audience=[RECEIVER], now=NOW)
    result_ok = mint_result(r3, summar, OUTPUT, invocation_jws=inv_ok, now=NOW)
    h_b, p_b, _ = result_ok.split(".")  # attacker re-signs, kid/payload kept
    result_forged = f"{h_b}.{p_b}.{b64u_encode(attacker.sign(f'{h_b}.{p_b}'.encode()))}"
    result_mismatch = mint_result(alt_r3, summar, OUTPUT, now=NOW)

    vectors = [
        vec("v01_happy_path", "4-delegation chain, valid invocation",
            chain, inv_ok, {"allowed": True, "error": None}),
        vec("v02_scope_widened", "leaf re-signed with widened scope",
            chain[:3] + [widened], None, {"allowed": False, "error": "ERR_SCOPE_WIDENED"}),
        vec("v03_linkage_break", "hop issuer is not parent subject",
            chain[:3] + [rogue], None, {"allowed": False, "error": "ERR_LINKAGE"}),
        vec("v04_parent_hash_splice", "structurally-identical parent, different bytes",
            [r0, r1, alt_r2, r3], None, {"allowed": False, "error": "ERR_PARENT_HASH"}),
        vec("v05_expired", "verified 2h after mint of 1h receipts",
            chain, None, {"allowed": False, "error": "ERR_EXPIRED"}, {"now": NOW + 7200}),
        vec("v06_stolen_chain", "invocation signed by non-subject",
            chain, inv_stolen, {"allowed": False, "error": "ERR_POP"}),
        vec("v07_untrusted_principal", "root principal outside trust list",
            chain, inv_ok, {"allowed": False, "error": "ERR_ROOT_UNTRUSTED"},
            {"trusted_principals": ["did:web:someone-else.example"]}),
        vec("v08_assurance_floor", "policy requires L1, chain is L0",
            chain, None, {"allowed": False, "error": "ERR_ASSURANCE"}, {"min_assurance": 1}),
        vec("r01_valid_result", "leaf subject attests outcome, bound to leaf receipt + invocation",
            chain, None, {"allowed": True, "error": None}, result=result_ok),
        vec("r02_wrong_signer", "result re-signed by non-subject, kid/payload kept",
            chain, None, {"allowed": False, "error": "ERR_RESULT_SIG"}, result=result_forged),
        vec("r03_receipt_mismatch", "result bound to a different leaf receipt's bytes",
            chain, None, {"allowed": False, "error": "ERR_RESULT_BINDING"}, result=result_mismatch),
    ]

    OUT.mkdir(exist_ok=True)
    for v in vectors:
        (OUT / f"{v['name']}.json").write_text(json.dumps(v, indent=2))
    print(f"wrote {len(vectors)} vectors to {OUT}")


if __name__ == "__main__":
    main()
