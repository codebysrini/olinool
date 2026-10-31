"""Profile-seam tests (design §5, ratified 2026-07-05).

Covers the four profile behaviors the split adds, none of which touches a valid
jws-1 artifact's bytes or verdict:
  * unknown/disallowed profile -> ERR_PROFILE_NOT_ALLOWED (before claim logic)
  * mixed-profile chain         -> ERR_PROFILE_MIXED
  * unknown-profile invocation  -> rejected (ERR_PROFILE_NOT_ALLOWED)
  * a valid jws-1 chain under the default allow-list still verifies

Selection is by the artifact's own markers + the policy allow-list, never by
negotiation (instinct 9 / c20 generalized to encodings).
"""
from __future__ import annotations

import json

import pytest

from olinool import KeyResolver, Policy, Signer, attenuate, invoke, mint_root, verify_chain, verify_invocation
from olinool.core import b64u_decode, b64u_encode, canonical_json
from olinool.errors import ERR_PROFILE_MIXED, ERR_PROFILE_NOT_ALLOWED
from olinool import profiles

NOW = 1_700_000_000
REQ = b'{"m":"GET","p":"/x"}'
RECEIVER = "did:web:tools.example"


def _resign(jws: str, signer: Signer, mutate_header=None, mutate_payload=None) -> str:
    h_b, p_b, _ = jws.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    if mutate_header:
        mutate_header(header)
    if mutate_payload:
        mutate_payload(payload)
    h2 = b64u_encode(canonical_json(header))
    p2 = b64u_encode(canonical_json(payload))
    sig = b64u_encode(signer.sign(f"{h2}.{p2}".encode()))
    return f"{h2}.{p2}.{sig}"


@pytest.fixture
def world():
    P = Signer.generate("did:web:acme.example")
    A = Signer.generate("did:web:acme.example:agent")
    resolver = KeyResolver()
    for s in (P, A):
        resolver.register_signer(s)
    root = mint_root(P, A.agent_id, scope=[{"act": "call", "res": "tool/*"}],
                     ttl_s=3600, max_depth=4, audience=[RECEIVER], now=NOW)
    return dict(P=P, A=A, resolver=resolver, root=root)


class _StubProfile:
    """A throwaway second profile for the mixed-chain test. Differentiates by
    HEADER typ so the payload still passes the jws-1 claim schema (v=0.1),
    letting the chain reach the uniform-profile check."""
    id = "jws-2-test"
    STUB_TYP = "olinool-receipt-v2+jws"

    def matches(self, header, claims):
        return header.get("typ") == self.STUB_TYP

    def verify_sig(self, decoded, resolver, agent_id):
        return resolver.verify(agent_id, decoded.signing_input, decoded.sig)


def test_p01_default_allow_list_still_verifies(world):
    d = verify_chain([world["root"]], world["resolver"], Policy(), now=NOW)
    assert d.allowed, d


def test_p02_empty_allow_list_denies_profile(world):
    pol = Policy(allowed_profiles=set())          # nothing allowed, not even jws-1
    d = verify_chain([world["root"]], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_NOT_ALLOWED


def test_p03_unknown_version_is_profile_not_allowed(world):
    # A receipt with the receipt typ but v="9.9" matches NO profile -> rejected
    # before claim logic (this is the intended reroute: was ERR_STRUCTURE).
    bad = _resign(world["root"], world["P"], mutate_payload=lambda p: p.__setitem__("v", "9.9"))
    d = verify_chain([bad], world["resolver"], Policy(), now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_NOT_ALLOWED


def test_p04_mixed_profile_chain_rejected(world):
    profiles.register(_StubProfile())
    try:
        # hop1: a valid attenuation, re-tagged to the stub profile's header typ
        # and re-signed by its issuer (world["A"] == root.sub).
        B = Signer.generate("did:web:acme.example:worker")
        world["resolver"].register_signer(B)
        hop1 = attenuate(world["root"], world["A"], B.agent_id,
                         scope=[{"act": "call", "res": "tool/search*"}], now=NOW)
        hop1_stub = _resign(hop1, world["A"],
                            mutate_header=lambda h: h.__setitem__("typ", _StubProfile.STUB_TYP))
        pol = Policy(allowed_profiles={"jws-1", "jws-2-test"})   # both allowed, but mixed
        d = verify_chain([world["root"], hop1_stub], world["resolver"], pol, now=NOW)
        assert not d.allowed and d.error == ERR_PROFILE_MIXED
    finally:
        profiles.unregister("jws-2-test")


def test_p05_unknown_profile_invocation_rejected(world):
    # Valid jws-1 chain, but the invocation is re-tagged to an unregistered
    # profile typ -> rejected, not silently accepted (the two artifacts must
    # share the chain's profile).
    inv = invoke(world["root"], world["A"], RECEIVER, REQ, now=NOW)
    forged = _resign(inv, world["A"],
                     mutate_header=lambda h: h.__setitem__("typ", "olinool-invocation-v2+jws"))
    d = verify_invocation([world["root"]], forged, REQ, RECEIVER, world["resolver"], Policy(), now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_NOT_ALLOWED
