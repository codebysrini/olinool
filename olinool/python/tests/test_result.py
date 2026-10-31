"""olinool-result outcome records — mint guards, verification, hash bindings.

Every test maps to a claimed property of spec §14: only the leaf subject can
produce a verifiable result, and the record is bound to the exact leaf
receipt bytes (and optionally the invocation) it attests to.
"""
from __future__ import annotations

import json
import time

import pytest

from olinool import (
    KeyResolver,
    MintError,
    Signer,
    attenuate,
    invoke,
    mint_result,
    mint_root,
    verify_result,
)
from olinool.core import b64u_decode, b64u_encode, canonical_json, sha256_b64u
from olinool.errors import ERR_RESULT_BINDING, ERR_RESULT_SIG, ERR_RESULT_STRUCTURE

NOW = int(time.time())
RECEIVER = "did:web:data.example"
REQ = b'{"method":"GET","path":"/datasets/eu-42"}'
OUTPUT = b"Summary: revenue was 42.0M"


@pytest.fixture(scope="module")
def world():
    principal = Signer.generate("did:web:acme.example")
    agent = Signer.generate("did:web:acme.example:worker")
    attacker = Signer.generate("did:web:evil.example:mallory")
    resolver = KeyResolver()
    for s in (principal, agent, attacker):
        resolver.register_signer(s)
    receipt = mint_root(principal, agent.agent_id,
                        scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 5}}],
                        ttl_s=600, max_depth=1, now=NOW)
    # structurally identical authority, different bytes (fresh rid/signature)
    alt_receipt = mint_root(principal, agent.agent_id,
                            scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 5}}],
                            ttl_s=600, max_depth=1, now=NOW)
    return dict(principal=principal, agent=agent, attacker=attacker,
                resolver=resolver, receipt=receipt, alt_receipt=alt_receipt)


def resign_keep_kid(jws: str, signer: Signer) -> str:
    """Re-sign an existing JWS with another key, leaving header/payload bytes as-is."""
    h_b, p_b, _ = jws.split(".")
    return f"{h_b}.{p_b}.{b64u_encode(signer.sign(f'{h_b}.{p_b}'.encode()))}"


def test_r01_valid_result_verifies(world):
    inv = invoke(world["receipt"], world["agent"], RECEIVER, REQ, now=NOW)
    res = mint_result(world["receipt"], world["agent"], OUTPUT,
                      invocation_jws=inv, now=NOW)
    d = verify_result(res, world["receipt"], world["resolver"])
    assert d.allowed, d
    payload = json.loads(b64u_decode(res.split(".")[1]))
    assert payload["out"] == sha256_b64u(OUTPUT)
    assert payload["inv"] == sha256_b64u(inv.encode("ascii"))
    assert payload["rcp"] == sha256_b64u(world["receipt"].encode("ascii"))


def test_r02_wrong_signer_rejected(world):
    # Attacker re-signs a genuine result, keeping kid == sub == leaf subject.
    res = mint_result(world["receipt"], world["agent"], OUTPUT, now=NOW)
    forged = resign_keep_kid(res, world["attacker"])
    d = verify_result(forged, world["receipt"], world["resolver"])
    assert not d.allowed and d.error == ERR_RESULT_SIG


def test_r03_receipt_mismatch_rejected(world):
    # Result minted against a different (equally valid) receipt's bytes.
    res = mint_result(world["alt_receipt"], world["agent"], OUTPUT, now=NOW)
    d = verify_result(res, world["receipt"], world["resolver"])
    assert not d.allowed and d.error == ERR_RESULT_BINDING


def test_r04_tampered_payload_rejected(world):
    res = mint_result(world["receipt"], world["agent"], OUTPUT,
                      status="failed", now=NOW)
    h_b, p_b, s_b = res.split(".")
    payload = json.loads(b64u_decode(p_b))
    payload["status"] = "completed"  # launder a failure into a success
    tampered = f"{h_b}.{b64u_encode(canonical_json(payload))}.{s_b}"
    d = verify_result(tampered, world["receipt"], world["resolver"])
    assert not d.allowed and d.error == ERR_RESULT_SIG


def test_r05_mint_guards(world):
    with pytest.raises(MintError):  # actor is not the leaf subject
        mint_result(world["receipt"], world["attacker"], OUTPUT, now=NOW)
    with pytest.raises(MintError):  # status outside the closed enum
        mint_result(world["receipt"], world["agent"], OUTPUT, status="done", now=NOW)
    with pytest.raises(MintError):  # ver outside the closed enum
        mint_result(world["receipt"], world["agent"], OUTPUT, ver="notary", now=NOW)


def test_r06_wrong_typ_is_structural(world):
    # A receipt presented as a result must fail structurally, not on signature.
    d = verify_result(world["receipt"], world["receipt"], world["resolver"])
    assert not d.allowed and d.error == ERR_RESULT_STRUCTURE
