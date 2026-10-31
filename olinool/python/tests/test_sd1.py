"""sd-1 profile tests (SPEC §16, Python codec 2026-07-07).

Covers the SD-JWT selective-disclosure behaviors §16 defines, none of which
touches a jws-1 artifact's bytes or verdict (golden-bytes + frozen corpus
prove that separately):
  * mint/verify round trip — disclosable claims (rid, asr.evidence) hidden in
    the issuer-signed base, resolved from presented disclosures
  * holder withholding: optional claim (evidence) -> still allowed; required
    claim (rid) -> fail closed at R1b (ERR_STRUCTURE)
  * disclosure tamper -> digest matches no _sd -> ERR_STRUCTURE (§16.2)
  * R5/rcp preimage = issuer-signed base, stable across withheld disclosures
    (§16.4) — for chains AND for invocation leaf binding
  * uniform-profile rule: jws-1/sd-1 mixes -> ERR_PROFILE_MIXED (§15) — the
    behavior test_profiles p04 could only exercise via a stub, now real
  * envelope-family gate: a plain JWS re-tagged with sd-jwt typ markers can
    never select sd-1 (the ~-structure half of the REGISTRY predicate)
  * _sd_alg pinned to sha-256 (§16.1, instinct 9)
  * mint-side guards: unknown profile / cross-profile attenuation -> MintError
"""
from __future__ import annotations

import json

import pytest

from olinool import (
    KeyResolver,
    Policy,
    Signer,
    attenuate,
    invoke,
    mint_root,
    verify_chain,
    verify_invocation,
)
from olinool.core import b64u_decode, b64u_encode, canonical_json, sha256_b64u
from olinool.errors import ERR_PROFILE_MIXED, ERR_PROFILE_NOT_ALLOWED, ERR_STRUCTURE, MintError
from olinool.muthirai import receipt_hash
from olinool.profiles.sd1 import SD1_PROFILE

NOW = 1_700_000_000
RECEIVER = "did:web:tools.example"
REQ = b'{"m":"GET","p":"/x"}'


def _sd_policy(**kw) -> Policy:
    return Policy(allowed_profiles={"sd-1"}, **kw)


# --- combined-form helpers (holder-side presentation editing) -----------------

def _split(combined: str):
    assert combined.endswith("~"), "sd-1 combined form must end with '~'"
    segments = combined[:-1].split("~")
    return segments[0], segments[1:]


def _join(base: str, disclosures) -> str:
    return "~".join([base, *disclosures]) + "~"


def _disclosure_name(d: str) -> str:
    return json.loads(b64u_decode(d))[1]


def withhold(combined: str, claim_name: str) -> str:
    """Holder drops the named claim's disclosure from the presentation."""
    base, discs = _split(combined)
    return _join(base, [d for d in discs if _disclosure_name(d) != claim_name])


def tamper(combined: str, claim_name: str, new_value) -> str:
    """Attacker mutates a disclosure's value: its digest no longer appears in
    the signed _sd array."""
    base, discs = _split(combined)
    out = []
    for d in discs:
        arr = json.loads(b64u_decode(d))
        if arr[1] == claim_name:
            arr[2] = new_value
            d = b64u_encode(canonical_json(arr))
        out.append(d)
    return _join(base, out)


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
    return f"{h2}.{p2}.{b64u_encode(signer.sign(f'{h2}.{p2}'.encode()))}"


@pytest.fixture
def world():
    P = Signer.generate("did:web:acme.example")
    A = Signer.generate("did:web:acme.example:agent")
    B = Signer.generate("did:web:acme.example:worker")
    resolver = KeyResolver()
    for s in (P, A, B):
        resolver.register_signer(s)
    root = mint_root(P, A.agent_id, scope=[{"act": "call", "res": "tool/*"}],
                     ttl_s=3600, max_depth=4, now=NOW, profile="sd-1")
    leaf = attenuate(root, A, B.agent_id, scope=[{"act": "call", "res": "tool/search*"}],
                     audience=[RECEIVER], now=NOW)  # profile inherited: sd-1
    return dict(P=P, A=A, B=B, resolver=resolver, root=root, leaf=leaf)


def test_sd1_mint_and_verify_roundtrip(world):
    # Wire shape: combined form; rid/evidence hidden in the base; the linkage
    # set (§16.3) — and aud, per the widening-channel design note — cleartext.
    for art, n_disc in ((world["root"], 2), (world["leaf"], 2)):
        base, discs = _split(art)
        assert len(discs) == n_disc  # rid + asr.evidence
        base_payload = json.loads(b64u_decode(base.split(".")[1]))
        assert "rid" not in base_payload
        assert base_payload["_sd_alg"] == "sha-256"
        assert len(base_payload["_sd"]) == 1
        assert "evidence" not in base_payload["asr"] and "_sd" in base_payload["asr"]
        for mandatory in ("v", "pri", "iss", "sub", "scope", "cst", "asr"):
            assert mandatory in base_payload
    leaf_base_payload = json.loads(b64u_decode(_split(world["leaf"])[0].split(".")[1]))
    assert leaf_base_payload["aud"] == [RECEIVER]  # aud never hidden (R11 widening)

    d = verify_chain([world["root"], world["leaf"]], world["resolver"], _sd_policy(), now=NOW)
    assert d.allowed, d
    assert d.effective_scope == [{"act": "call", "res": "tool/search*"}]


def test_sd1_not_in_default_allowlist(world):
    d = verify_chain([world["root"]], world["resolver"], Policy(), now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_NOT_ALLOWED


def test_sd1_withholding_evidence_still_verifies_and_r5_holds(world):
    # Withholding on BOTH hops: the parent's combined form changes, but the
    # child's prh binds the parent's issuer-signed base (§16.4), so the chain
    # still verifies — selective disclosure without wire re-issue.
    chain = [withhold(world["root"], "evidence"), withhold(world["leaf"], "evidence")]
    d = verify_chain(chain, world["resolver"], _sd_policy(), now=NOW)
    assert d.allowed, d


def test_sd1_withholding_required_rid_fails_closed(world):
    # rid is disclosable but R1b's schema requires it: withheld -> ERR_STRUCTURE
    # (fail closed, §16.2 — hidden never verifies as absent-but-fine).
    chain = [world["root"], withhold(world["leaf"], "rid")]
    d = verify_chain(chain, world["resolver"], _sd_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_STRUCTURE


def test_sd1_tampered_disclosure_rejected(world):
    # Mutated disclosure -> digest matches no signed _sd entry -> ERR_STRUCTURE.
    chain = [world["root"], tamper(world["leaf"], "rid", "evil-rid")]
    d = verify_chain(chain, world["resolver"], _sd_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_STRUCTURE


def test_sd1_invocation_binds_leaf_base_across_disclosure_choices(world):
    # Hand-built sd-1 invocation (no mint path yet): rcp binds the LEAF BASE
    # (§16.4), so the same invocation verifies even when the holder presents
    # the leaf with a disclosure withheld.
    leaf_base, _ = _split(world["leaf"])
    inv = SD1_PROFILE.serialize(world["B"], SD1_PROFILE.invocation_typ, {
        "typ": "olinool-invocation",
        "rcp": receipt_hash(leaf_base),
        "sub": world["B"].agent_id,
        "aud": RECEIVER,
        "req": sha256_b64u(REQ),
        "iat": NOW,
        "nnc": "sd1-nonce-1",
    })
    assert inv.endswith("~") and _split(inv)[1] == []  # no disclosable claims (§16.1)
    chain = [world["root"], withhold(world["leaf"], "evidence")]
    d = verify_invocation(chain, inv, REQ, RECEIVER, world["resolver"], _sd_policy(), now=NOW)
    assert d.allowed, d


def test_sd1_jws1_invocation_on_sd1_chain_is_mixed(world):
    inv = invoke(world["leaf"], world["B"], RECEIVER, REQ, now=NOW)  # jws-1 artifact
    pol = Policy(allowed_profiles={"jws-1", "sd-1"})
    d = verify_invocation([world["root"], world["leaf"]], inv, REQ, RECEIVER,
                          world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_MIXED


def test_sd1_mixed_chain_rejected(world):
    # jws-1 root + hand-built sd-1 hop (both allowed) -> ERR_PROFILE_MIXED.
    # This is the REAL two-profile mix test_profiles p04 could only stub.
    r0 = mint_root(world["P"], world["A"].agent_id,
                   scope=[{"act": "call", "res": "tool/*"}], ttl_s=3600, max_depth=4, now=NOW)
    hop1 = SD1_PROFILE.serialize(world["A"], SD1_PROFILE.receipt_typ, {
        "v": "0.1",
        "rid": "00000000-0000-0000-0000-00000000sd01",
        "prh": receipt_hash(r0),  # jws-1 parent preimage = verbatim wire (§16.4)
        "pri": world["P"].agent_id,
        "iss": world["A"].agent_id,
        "sub": world["B"].agent_id,
        "scope": [{"act": "call", "res": "tool/search*"}],
        "cst": {"iat": NOW, "exp": NOW + 1800, "max_depth": 3, "epoch": 0},
        "asr": {"level": 0, "evidence": None},
    })
    pol = Policy(allowed_profiles={"jws-1", "sd-1"})
    d = verify_chain([r0, hop1], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_MIXED


def test_sd1_typ_on_plain_jws_is_not_sd1(world):
    # Envelope-family gate: a compact JWS re-tagged with sd-1's typ (valid
    # signature) must NOT select sd-1 — the ~-structure is half the predicate.
    r0 = mint_root(world["P"], world["A"].agent_id,
                   scope=[{"act": "call", "res": "tool/*"}], ttl_s=3600, now=NOW)
    bad = _resign(r0, world["P"],
                  mutate_header=lambda h: h.__setitem__("typ", "olinool-receipt+sd-jwt"))
    pol = Policy(allowed_profiles={"jws-1", "sd-1"})
    d = verify_chain([bad], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_PROFILE_NOT_ALLOWED


def test_sd1_sd_alg_is_pinned(world):
    # _sd_alg is pinned to sha-256 (§16.1): any other value is structural
    # failure, never negotiated (instinct 9).
    base, discs = _split(world["root"])
    base2 = _resign(base, world["P"],
                    mutate_payload=lambda p: p.__setitem__("_sd_alg", "sha-3-256"))
    d = verify_chain([_join(base2, discs)], world["resolver"], _sd_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_STRUCTURE


def test_sd1_mint_guards(world):
    scope = [{"act": "call", "res": "tool/search*"}]
    with pytest.raises(MintError):  # unknown profile id
        mint_root(world["P"], world["A"].agent_id, scope=scope, now=NOW, profile="jws-9")
    with pytest.raises(MintError):  # sd-1 child under jws-1 parent (§15 uniform)
        r0 = mint_root(world["P"], world["A"].agent_id,
                       scope=[{"act": "call", "res": "tool/*"}], ttl_s=3600, now=NOW)
        attenuate(r0, world["A"], world["B"].agent_id, scope=scope, now=NOW, profile="sd-1")
    with pytest.raises(MintError):  # jws-1 child under sd-1 parent
        attenuate(world["root"], world["A"], world["B"].agent_id, scope=scope,
                  now=NOW, profile="jws-1")
