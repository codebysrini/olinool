#!/usr/bin/env python3
"""Generate the §15 profile-rejection vectors (v09+) — ADDITIVE ONLY.

Corpus law (AINTIRAM MURAI): frozen corpora are wire-format law; generators
add, never rewrite. This script writes ONLY the vectors named below and
REFUSES to run if any of them already exist. It never touches v01–v08/r01–r03
(those stay exactly as gen_corpus.py minted them).

Vectors (batch 2026-07-05, frozen):
  v09_profile_not_allowed             chain slot: valid jws-1 chain, but the
                                      policy allow-list contains only sd-1
                                      (reserved, not built) -> the artifact's
                                      profile is not allowed, rejected before
                                      any claim logic.
  v10_profile_not_allowed_invocation  invocation slot: chain passes (jws-1
                                      allowed), but the invocation's typ marker
                                      matches no registered profile -> rejected
                                      at the R12 profile gate, before PoP checks.

Vectors (batch 2026-07-07 — fills the remaining NOT_ALLOWED slots/causes):
  v11_profile_not_allowed_result      RESULT slot (v09=chain, v10=invocation,
                                      v11=result): valid jws-1 result + leaf,
                                      but the allow-list is {sd-1} only ->
                                      rejected before the binding check.
  v12_profile_bad_version_receipt     chain slot, data-side cause: receipt with
                                      the correct typ, VALID signature, but
                                      payload v="9.9" matches no registered
                                      profile -> selection returns None before
                                      claim logic (the v0.3 reroute: was
                                      ERR_STRUCTURE; mirrors test_profiles p03).
  v13_profile_empty_allowlist_chain   chain slot, policy-side cause: fully valid
                                      jws-1 chain under an explicit EMPTY
                                      allow-list (nothing allowed, not even
                                      jws-1) -> rejected (mirrors p02).

Vectors (batch 2026-07-07-mixed — the previously GATED ERR_PROFILE_MIXED pair):
  v14_profile_mixed_chain             chain slot: hop0 jws-1, hop1 a hand-built
                                      sd-1 receipt that is otherwise FULLY valid
                                      (validly signed, prh binds hop0's exact
                                      bytes, scope/window nested) under an
                                      allow-list containing BOTH profiles ->
                                      only the §15 uniform-profile rule fires.
  v15_profile_mixed_invocation        invocation slot: fully valid sd-1 chain,
                                      jws-1 invocation minted against its leaf,
                                      both profiles allowed -> the R12 profile
                                      gate rejects the cross-profile exercise.

History of the MIXED gate (finding 2026-07-05, retired 2026-07-07): a MIXED
verdict requires two artifacts that each classify as a DIFFERENT
registered-and-allowed profile, and v0.3 registered exactly one (jws-1), so
ERR_PROFILE_MIXED was structurally unreachable from data-only vectors — and a
vector authored while the TS selectProfile was still hardcoded jws-1-only
would have encoded a Py/TS divergence (Python ERR_PROFILE_MIXED vs TS
ERR_PROFILE_NOT_ALLOWED — AINTIRAM instinct 14). The gate condition was: a
second REAL profile in BOTH verifiers. It was met 2026-07-07 when sd-1 landed
in the Python registry (profiles/sd1.py) and in typescript/src/verify.ts
(registry-mirroring selectProfile + SD-JWT decode), certified by identical
verdicts over the full corpus; v14/v15 were authored the same day.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import uuid

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from olinool import Signer, attenuate, invoke, mint_result, mint_root  # noqa: E402
from olinool.core import b64u_decode, b64u_encode, canonical_json  # noqa: E402
from olinool.muthirai import receipt_hash  # noqa: E402
from olinool.profiles.sd1 import SD1_PROFILE  # noqa: E402

NOW = int(time.time())
RECEIVER = "did:web:data.example"
REQ = b'{"method":"GET","path":"/datasets/eu-42"}'
OUTPUT = b"Summary: 3 rows from eu-42"
OUT = pathlib.Path(__file__).resolve().parent.parent / "python" / "olinool" / "conformance" / "vectors"

# Each batch, once written, is frozen wire-format law. Later batches ADD names;
# earlier lists are never edited and their files never rewritten.
BATCHES = {
    "2026-07-05": ["v09_profile_not_allowed", "v10_profile_not_allowed_invocation"],
    "2026-07-07": ["v11_profile_not_allowed_result", "v12_profile_bad_version_receipt",
                   "v13_profile_empty_allowlist_chain"],
    "2026-07-07-mixed": ["v14_profile_mixed_chain", "v15_profile_mixed_invocation"],
}
VECTOR_NAMES = [n for names in BATCHES.values() for n in names]


def retag_header(jws: str, signer: Signer, typ: str) -> str:
    """Re-sign an artifact with a mutated header `typ` (profile marker).

    The signature is VALID for the signer — only the profile predicate should
    fire, proving the gate sits before, and independent of, PoP checks."""
    h_b, p_b, _ = jws.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    header["typ"] = typ
    h2 = b64u_encode(canonical_json(header))
    p2 = b64u_encode(canonical_json(payload))
    return f"{h2}.{p2}.{b64u_encode(signer.sign(f'{h2}.{p2}'.encode()))}"


def retag_version(jws: str, signer: Signer, v: str) -> str:
    """Re-sign a receipt with a mutated payload `v` (profile version marker).

    Same trick as retag_header: the signature is VALID for the signer — the
    correct typ + unknown version matches NO registered profile, so only the
    selection gate fires (before claim logic, which would call v="9.9"
    ERR_STRUCTURE — the v0.3 reroute)."""
    h_b, p_b, _ = jws.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    payload["v"] = v
    h2 = b64u_encode(canonical_json(header))
    p2 = b64u_encode(canonical_json(payload))
    return f"{h2}.{p2}.{b64u_encode(signer.sign(f'{h2}.{p2}'.encode()))}"


def main() -> None:
    # Corpus-law guard (add-only): a batch whose files all exist is frozen and
    # skipped; a PARTIALLY present batch means someone deleted frozen law —
    # refuse (restore from git; fixes ship as NEW names). If every batch is
    # frozen there is nothing this script may legally write.
    to_write: set = set()
    for stamp, names in BATCHES.items():
        present = [n for n in names if (OUT / f"{n}.json").exists()]
        if len(present) == len(names):
            continue  # frozen batch — never rewritten
        if present:
            sys.exit(f"REFUSING: batch {stamp} is partially present ({present}); frozen "
                     "vectors are never regenerated — restore from git (corpus law).")
        to_write.update(names)
    if not to_write:
        sys.exit(f"REFUSING to regenerate frozen vectors: {VECTOR_NAMES} already exist. "
                 "Fixes ship as NEW vector files, never rewrites (corpus law).")

    principal = Signer.generate("did:web:acme.example")
    orch = Signer.generate("did:web:acme.example:orchestrator")
    worker = Signer.generate("did:web:vendor.example:worker")
    signers = [principal, orch, worker]
    keys = {s.agent_id: s.public_key_b64u for s in signers}

    r0 = mint_root(principal, orch.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 50}}],
                   ttl_s=3600, max_depth=4, now=NOW)
    r1 = attenuate(r0, orch, worker.agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
                   audience=[RECEIVER], now=NOW)
    chain = [r0, r1]
    inv_ok = invoke(chain[-1], worker, RECEIVER, REQ, now=NOW, nonce="vec-nonce-p1")
    # Valid signature by the leaf subject, but a typ marker no profile claims:
    # selection returns None at the invocation slot.
    inv_alien = retag_header(inv_ok, worker, "olinool-invocation+sdjwt")
    # Valid signature by the hop's issuer (orch), correct receipt typ, but
    # payload v="9.9" matches no registered profile (v12).
    r1_badv = retag_version(r1, orch, "9.9")
    # Valid jws-1 result by the leaf subject, mirroring r01's shape (v11).
    result_ok = mint_result(chain[-1], worker, OUTPUT, invocation_jws=inv_ok, now=NOW)

    # --- 2026-07-07-mixed batch artifacts (ERR_PROFILE_MIXED, gate retired) ---
    # v14: a hand-built sd-1 hop under the jws-1 root — attenuate() correctly
    # REFUSES cross-profile minting (§15 mint guard), so the attacker's hop is
    # pressed directly through the sd-1 codec. It is otherwise FULLY valid:
    # validly signed by orch, prh binds r0's exact bytes (jws-1 preimage =
    # verbatim wire, SPEC §16.4), scope/window/depth properly nested — if a
    # verifier forgot the uniform-profile rule, this chain would VERIFY. Only
    # the §15 mixed gate stands between this vector and ALLOW.
    r1_sd_mixed = SD1_PROFILE.serialize(orch, SD1_PROFILE.receipt_typ, {
        "v": "0.1",
        "rid": str(uuid.uuid4()),
        "prh": receipt_hash(r0),
        "pri": principal.agent_id,
        "iss": orch.agent_id,
        "sub": worker.agent_id,
        "scope": [{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
        "cst": {"iat": NOW, "exp": NOW + 1800, "max_depth": 3, "epoch": 0},
        "asr": {"level": 0, "evidence": None},
        "aud": [RECEIVER],
    })
    # v15: a fully valid sd-1 chain + a jws-1 invocation minted against its
    # leaf. The chain alone verifies (both profiles allowed); the R12 profile
    # gate then rejects exercising an sd-1 chain with a jws-1 invocation.
    s0 = mint_root(principal, orch.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 50}}],
                   ttl_s=3600, max_depth=4, now=NOW, profile="sd-1")
    s1 = attenuate(s0, orch, worker.agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
                   audience=[RECEIVER], now=NOW)  # profile inherited: sd-1
    inv_jws1_on_sd = invoke(s1, worker, RECEIVER, REQ, now=NOW, nonce="vec-nonce-p2")

    def vec(name, description, chain_, invocation, expect, policy_extra=None, result=None):
        v = dict(
            name=name, description=description, keys=keys, chain=chain_,
            invocation=invocation, request_b64=b64u_encode(REQ), receiver_id=RECEIVER,
            policy={"now": NOW, "min_assurance": 0, "trusted_principals": None,
                    **(policy_extra or {})},
            expect=expect,
        )
        if result is not None:  # only result-slot vectors carry the key
            v["result"] = result
        return v

    vectors = [
        vec("v09_profile_not_allowed",
            "valid jws-1 chain, policy allow-list is {sd-1} only",
            chain, None, {"allowed": False, "error": "ERR_PROFILE_NOT_ALLOWED"},
            {"allowed_profiles": ["sd-1"]}),
        vec("v10_profile_not_allowed_invocation",
            "chain passes; invocation typ marker matches no registered profile",
            chain, inv_alien, {"allowed": False, "error": "ERR_PROFILE_NOT_ALLOWED"},
            {"allowed_profiles": ["jws-1"]}),
        vec("v11_profile_not_allowed_result",
            "valid jws-1 result + leaf receipt, policy allow-list is {sd-1} only",
            chain, None, {"allowed": False, "error": "ERR_PROFILE_NOT_ALLOWED"},
            {"allowed_profiles": ["sd-1"]}, result=result_ok),
        vec("v12_profile_bad_version_receipt",
            "receipt with valid signature but payload v=9.9 matches no profile",
            [r0, r1_badv], None, {"allowed": False, "error": "ERR_PROFILE_NOT_ALLOWED"}),
        vec("v13_profile_empty_allowlist_chain",
            "fully valid jws-1 chain under an explicit empty allow-list",
            chain, None, {"allowed": False, "error": "ERR_PROFILE_NOT_ALLOWED"},
            {"allowed_profiles": []}),
        vec("v14_profile_mixed_chain",
            "hop0 jws-1, hop1 sd-1 (validly signed, prh binds hop0's exact "
            "bytes, scope/window nested — otherwise verifiable); both profiles "
            "allowed -> only the §15 uniform-profile rule fires",
            [r0, r1_sd_mixed], None, {"allowed": False, "error": "ERR_PROFILE_MIXED"},
            {"allowed_profiles": ["jws-1", "sd-1"]}),
        vec("v15_profile_mixed_invocation",
            "fully valid sd-1 chain exercised with a jws-1 invocation; both "
            "profiles allowed -> the R12 profile gate rejects the cross-profile "
            "exercise",
            [s0, s1], inv_jws1_on_sd, {"allowed": False, "error": "ERR_PROFILE_MIXED"},
            {"allowed_profiles": ["jws-1", "sd-1"]}),
    ]

    written = 0
    for v in vectors:
        if v["name"] not in to_write:
            continue  # frozen batch member — leave its bytes exactly as minted
        (OUT / f"{v['name']}.json").write_text(json.dumps(v, indent=2))
        written += 1
    print(f"wrote {written} vectors to {OUT} (additive; existing corpus untouched)")
    print("NOTE: ERR_PROFILE_MIXED is corpus-asserted since 2026-07-07 (v14 chain, "
          "v15 invocation) — the two-real-profiles-in-both-verifiers gate is "
          "retired; see module docstring for its history.")


if __name__ == "__main__":
    main()
