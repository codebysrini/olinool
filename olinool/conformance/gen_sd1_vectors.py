#!/usr/bin/env python3
"""Generate the sd-1 (SD-JWT, RFC 9901 — SPEC §16) conformance vectors — ADDITIVE ONLY.

Corpus law (AINTIRAM MURAI): frozen corpora are wire-format law; generators
add, never rewrite. This script writes ONLY the vectors named below and
REFUSES to run if any of them already exist. It never touches
v01–v13/r01–r03 (those stay exactly as their generators minted them).

Vectors (batch 2026-07-07, sd-1 Python codec):
  sd01_valid_chain_redacted   chain slot, ALLOWED: a valid 2-hop sd-1 chain.
                              Disclosable claims (rid, asr.evidence) are hidden
                              behind salted-hash disclosures in each hop's
                              issuer-signed base; the holder presents the rid
                              disclosures (R1b requires rid) but WITHHOLDS the
                              asr.evidence disclosure on BOTH hops. Verifies
                              because (a) no rule reads evidence and (b) the
                              child's prh binds the parent's ISSUER-SIGNED BASE
                              (§16.4), which is unchanged by holder-selected
                              disclosures.
  sd02_disclosure_tampered    chain slot, REJECTED: same chain, but the leaf's
                              rid disclosure value is mutated. Its digest no
                              longer appears in the signed _sd array ->
                              structural failure in decode (§16.2) ->
                              ERR_STRUCTURE. No new error codes.

Vectors (batch 2026-07-07-sd1-invocation — the sd-1 invocation binding path):
  sd03_valid_invocation_redacted_leaf   invocation slot, ALLOWED: a valid sd-1
                              chain (evidence withheld on both hops) exercised by
                              an sd-1 invocation whose rcp binds the leaf's
                              ISSUER-SIGNED BASE (§16.4). Verifies even though the
                              presented leaf dropped a disclosure — the corpus
                              assertion of §16.4 base-stability for invocations.
  sd04_invocation_rcp_binds_combined_form  invocation slot, REJECTED: the same
                              chain + an sd-1 invocation whose rcp instead hashes
                              the leaf's COMBINED presented form -> §16.4 preimage
                              mismatch -> ERR_POP. The cross-language REGRESSION
                              GUARD: a verifier that hashed the presented combined
                              form (not the base) would compute exactly this rcp
                              and wrongly ALLOW.

NAMING: the sd0x prefix carries single-profile sd-1 cases. The v14/v15 slots
were held RESERVED for the jws-1×sd-1 MIXED vectors while sd-1 existed in the
Python verifier only (instinct 14: authoring them earlier would have encoded a
Py/TS divergence). That gate RETIRED 2026-07-07: sd-1 landed in
typescript/src/verify.ts, both verifiers certify sd01/sd02 (and the full
corpus) with identical verdicts, and v14/v15 were authored the same day by
gen_profile_vectors.py. Assertion gap CLOSED 2026-07-07 by the
2026-07-07-sd1-invocation batch (sd03/sd04): the sd-1 invocation binding path
(rcp bound to the leaf's ISSUER-SIGNED BASE, SPEC §16.4) is now corpus-asserted
cross-language — accept (sd03) and the combined-form-preimage regression (sd04,
ERR_POP) — closing the TS hole that test_sd1.py could only cover in Python.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

for _sib in ("python", "../moolam/python", "../olinool/python"):
    sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent.parent / _sib).resolve()))

from olinool import Signer, attenuate, mint_root  # noqa: E402
from olinool.core import b64u_decode, b64u_encode, canonical_json, sha256_b64u  # noqa: E402
from olinool.muthirai import receipt_hash  # noqa: E402
from olinool.profiles.sd1 import SD1_PROFILE  # noqa: E402

NOW = int(time.time())
RECEIVER = "did:web:data.example"
REQ = b'{"method":"GET","path":"/datasets/eu-42"}'  # unused by chain-slot vectors; kept schema-uniform
OUT = pathlib.Path(__file__).resolve().parent.parent / "python" / "olinool" / "conformance" / "vectors"

# Each batch, once written, is frozen wire-format law. Later batches ADD names;
# earlier lists are never edited and their files never rewritten.
BATCHES = {
    "2026-07-07-sd1": ["sd01_valid_chain_redacted", "sd02_disclosure_tampered"],
    "2026-07-07-sd1-invocation": ["sd03_valid_invocation_redacted_leaf",
                                  "sd04_invocation_rcp_binds_combined_form"],
}
VECTOR_NAMES = [n for names in BATCHES.values() for n in names]


# --- holder-side presentation helpers (combined-form editing) -----------------

def _split(combined: str):
    assert combined.endswith("~")
    segments = combined[:-1].split("~")
    return segments[0], segments[1:]


def _join(base: str, disclosures) -> str:
    return "~".join([base, *disclosures]) + "~"


def withhold(combined: str, claim_name: str) -> str:
    """The holder drops the named claim's disclosure from the presentation."""
    base, discs = _split(combined)
    keep = [d for d in discs if json.loads(b64u_decode(d))[1] != claim_name]
    return _join(base, keep)


def tamper(combined: str, claim_name: str, new_value) -> str:
    """Attacker mutates a disclosure's value; the signed _sd digests no longer
    cover it."""
    base, discs = _split(combined)
    out = []
    for d in discs:
        arr = json.loads(b64u_decode(d))
        if arr[1] == claim_name:
            arr[2] = new_value
            d = b64u_encode(canonical_json(arr))
        out.append(d)
    return _join(base, out)


def main() -> None:
    # Corpus-law guard (add-only), identical to gen_profile_vectors.py: a batch
    # whose files all exist is frozen and skipped; a PARTIALLY present batch
    # means someone deleted frozen law — refuse (restore from git).
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
    keys = {s.agent_id: s.public_key_b64u for s in (principal, orch, worker)}

    r0 = mint_root(principal, orch.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 50}}],
                   ttl_s=3600, max_depth=4, now=NOW, profile="sd-1")
    r1 = attenuate(r0, orch, worker.agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
                   audience=[RECEIVER], now=NOW)  # profile inherited: sd-1

    # sd01: holder withholds the (rule-unread) asr.evidence disclosure on both
    # hops; rid disclosures presented (R1b requires rid).
    chain_redacted = [withhold(r0, "evidence"), withhold(r1, "evidence")]
    # sd02: leaf rid disclosure value mutated -> digest not in signed _sd.
    chain_tampered = [r0, tamper(r1, "rid", "evil-rid")]

    # sd03/sd04: the sd-1 invocation binding path (§16.4). Both present the same
    # redacted chain (chain_redacted, leaf = evidence withheld); they differ ONLY
    # in the invocation's rcp preimage. leaf_pres is the combined form actually in
    # the chain; leaf_base is its issuer-signed base (rcp's correct preimage).
    leaf_pres = chain_redacted[1]
    leaf_base = _split(r1)[0]

    def _sd_invocation(rcp: str, nonce: str) -> str:
        # Hand-built (invoke() still mints jws-1 by design, SPEC §16.1); mirrors
        # tests/test_sd1.py::test_sd1_invocation_binds_leaf_base_across_disclosure_choices.
        return SD1_PROFILE.serialize(worker, SD1_PROFILE.invocation_typ, {
            "typ": "olinool-invocation",
            "rcp": rcp,
            "sub": worker.agent_id,
            "aud": RECEIVER,
            "req": sha256_b64u(REQ),
            "iat": NOW,
            "nnc": nonce,
        })

    # sd03: rcp binds the issuer-signed base -> ACCEPT despite the withheld
    # disclosure (base is stable across holder disclosure choices, §16.4).
    inv_base = _sd_invocation(receipt_hash(leaf_base), "sd1-inv-base")
    # sd04: rcp binds the leaf's COMBINED presented form instead of the base ->
    # §16.4 preimage mismatch -> ERR_POP. A verifier that (wrongly) hashed the
    # presented combined form would compute exactly this rcp and ALLOW.
    inv_combined = _sd_invocation(receipt_hash(leaf_pres), "sd1-inv-combined")

    def vec(name, description, chain_, expect, invocation=None):
        return dict(
            name=name, description=description, keys=keys, chain=chain_,
            invocation=invocation, request_b64=b64u_encode(REQ), receiver_id=RECEIVER,
            policy={"now": NOW, "min_assurance": 0, "trusted_principals": None,
                    "allowed_profiles": ["sd-1"]},
            expect=expect,
        )

    vectors = [
        vec("sd01_valid_chain_redacted",
            "valid sd-1 chain; rid+asr.evidence hidden behind salted digests; "
            "evidence disclosure withheld on both hops -> still allowed "
            "(prh binds the issuer-signed base, SPEC §16.4)",
            chain_redacted, {"allowed": True, "error": None}),
        vec("sd02_disclosure_tampered",
            "sd-1 chain with the leaf's rid disclosure value mutated -> digest "
            "matches no signed _sd entry -> ERR_STRUCTURE (SPEC §16.2)",
            chain_tampered, {"allowed": False, "error": "ERR_STRUCTURE"}),
        vec("sd03_valid_invocation_redacted_leaf",
            "valid sd-1 chain (evidence withheld both hops) exercised by an sd-1 "
            "invocation whose rcp binds the leaf's ISSUER-SIGNED BASE (§16.4) -> "
            "ALLOWED even though the presented leaf dropped a disclosure",
            chain_redacted, {"allowed": True, "error": None}, invocation=inv_base),
        vec("sd04_invocation_rcp_binds_combined_form",
            "same sd-1 chain + an sd-1 invocation whose rcp hashes the leaf's "
            "COMBINED presented form instead of the issuer-signed base -> §16.4 "
            "preimage mismatch -> ERR_POP (regression guard: a verifier hashing "
            "the combined form would wrongly ALLOW)",
            chain_redacted, {"allowed": False, "error": "ERR_POP"}, invocation=inv_combined),
    ]

    written = 0
    for v in vectors:
        if v["name"] not in to_write:
            continue  # frozen batch member — leave its bytes exactly as minted
        (OUT / f"{v['name']}.json").write_text(json.dumps(v, indent=2))
        written += 1
    print(f"wrote {written} vectors to {OUT} (additive; existing corpus untouched)")
    print("NOTE: sd-1 is in BOTH verifiers since 2026-07-07 — sd01-sd04 certify "
          "Python and TypeScript identically (sd03/sd04 close the invocation-"
          "binding assertion gap, §16.4); the v14/v15 mixed vectors live in "
          "gen_profile_vectors.py (gate retired, see module docstrings).")


if __name__ == "__main__":
    main()
