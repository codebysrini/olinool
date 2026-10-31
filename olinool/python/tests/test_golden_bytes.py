"""Golden-bytes oracle for jws-1 parity (design §8.2).

This is the parity oracle for the v0.3 profile split: it pins the EXACT wire
bytes of a root receipt, one attenuation, and one invocation, minted under
fixed keys / fixed time / fixed rid / fixed nonce. The v0.1 = jws-1 refactor
MUST reproduce these bytes exactly — proving minting is byte-identical, not
merely verdict-identical. If any of these constants change, the wire changed:
that is a wire break (STOP), not a test to update.

Determinism controls (the only non-deterministic inputs in mint):
  * keys   — fixed 32-byte Ed25519 seeds (Ed25519 signing is deterministic)
  * time   — now= pinned
  * rid    — uuid4 monkeypatched to a fixed sequence
  * nonce  — invoke(nonce=...) pinned
Canonicalization (RFC 8785 JCS) and EdDSA are deterministic, so the bytes are
fully reproducible across the refactor.
"""
from __future__ import annotations

import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from moolam.core import canonical_json
from moolam.keys import Signer
from olinool.invocation import invoke
from olinool.muthirai import attenuate, mint_root

T = 1_700_000_000

# --- frozen golden capture (pre-refactor, current jws-1 behavior) -------------
GOLDEN_ROOT = "eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlIiwidHlwIjoib2xpbm9vbC1yZWNlaXB0K2p3cyJ9.eyJhc3IiOnsiZXZpZGVuY2UiOm51bGwsImxldmVsIjowfSwiY3N0Ijp7ImVwb2NoIjowLCJleHAiOjE3MDAwMDM2MDAsImlhdCI6MTcwMDAwMDAwMCwibWF4X2RlcHRoIjo0fSwiaXNzIjoiZGlkOndlYjphY21lLmV4YW1wbGUiLCJwcmgiOm51bGwsInByaSI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlIiwicmlkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMGExIiwic2NvcGUiOlt7ImFjdCI6ImNhbGwiLCJyZXMiOiJ0b29sLyoifV0sInN1YiI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlOmFzc2lzdGFudCIsInYiOiIwLjEifQ.BeJt40A_eBX_AebnA3CuDXkB95HENCAPcGDO-6giYFx5mqT2YDpFdH89NnymPK4XSTphtODdB1VfpclxIznVCg"
GOLDEN_ATT = "eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlOmFzc2lzdGFudCIsInR5cCI6Im9saW5vb2wtcmVjZWlwdCtqd3MifQ.eyJhc3IiOnsiZXZpZGVuY2UiOm51bGwsImxldmVsIjowfSwiY3N0Ijp7ImVwb2NoIjowLCJleHAiOjE3MDAwMDE4MDAsImlhdCI6MTcwMDAwMDAwMCwibWF4X2RlcHRoIjozfSwiaXNzIjoiZGlkOndlYjphY21lLmV4YW1wbGU6YXNzaXN0YW50IiwicHJoIjoiaGkxTTAyQVo3ZnFISFZqYmlDcXJYNmdJa0tiUlhkaHpLUTUwSlIzSGI1SSIsInByaSI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlIiwicmlkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMGEyIiwic2NvcGUiOlt7ImFjdCI6ImNhbGwiLCJyZXMiOiJ0b29sL3NlYXJjaCoifV0sInN1YiI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlOndvcmtlciIsInYiOiIwLjEifQ.tKYF_ZNQLOF1X491A4kOQdBI7xI8HuV34Kzz08bpD_bcjBPjyCdZD0idcDzWAn5jhP1CgxupKIjj2exiHwVxDw"
GOLDEN_INV = "eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDp3ZWI6YWNtZS5leGFtcGxlOndvcmtlciIsInR5cCI6Im9saW5vb2wtaW52b2NhdGlvbitqd3MifQ.eyJhdWQiOiJkaWQ6d2ViOnRvb2xzLmV4YW1wbGUiLCJpYXQiOjE3MDAwMDAwMDAsIm5uYyI6ImZpeGVkLW5vbmNlLTAwMCIsInJjcCI6IjRQQ2hkYzJROEF0NnNYeGVxc3hoNS1MMXQ4TXJyaXdPaVkwdUttYnB6S2ciLCJyZXEiOiJtSldlRFZuN0w4S1VPZndYX1R0RGdUZTlDS0pCVlpUR0hKRWlrUE5xMXdVIiwic3ViIjoiZGlkOndlYjphY21lLmV4YW1wbGU6d29ya2VyIiwidHlwIjoib2xpbm9vbC1pbnZvY2F0aW9uIn0.M_9ToYFBAUJRCaLsjFSFcY3dUhquT7pKN-BGcvAjYdzMGma41GS6cB2oPap1vcegEXf9kYkkwEOUpGBod3A4BA"


def _signers():
    P = Signer("did:web:acme.example", Ed25519PrivateKey.from_private_bytes(bytes([1] * 32)))
    A = Signer("did:web:acme.example:assistant", Ed25519PrivateKey.from_private_bytes(bytes([2] * 32)))
    B = Signer("did:web:acme.example:worker", Ed25519PrivateKey.from_private_bytes(bytes([3] * 32)))
    return P, A, B


def _mint_deterministic(monkeypatch):
    rids = iter([uuid.UUID(int=0xA1), uuid.UUID(int=0xA2), uuid.UUID(int=0xA3)])
    monkeypatch.setattr(uuid, "uuid4", lambda: next(rids))
    P, A, B = _signers()
    root = mint_root(P, A.agent_id, scope=[{"act": "call", "res": "tool/*"}],
                     ttl_s=3600, max_depth=4, now=T)
    att = attenuate(root, A, B.agent_id, scope=[{"act": "call", "res": "tool/search*"}],
                    ttl_s=1800, now=T)
    req = canonical_json({"tool": "search", "arguments": {"q": "acme"}})
    inv = invoke(att, B, "did:web:tools.example", req, now=T, nonce="fixed-nonce-000")
    return root, att, inv


def test_golden_bytes_jws1_parity(monkeypatch):
    root, att, inv = _mint_deterministic(monkeypatch)
    assert root == GOLDEN_ROOT, "root receipt bytes drifted — WIRE BREAK"
    assert att == GOLDEN_ATT, "attenuation bytes drifted — WIRE BREAK"
    assert inv == GOLDEN_INV, "invocation bytes drifted — WIRE BREAK"
