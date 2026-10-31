"""Adversarial conformance suite — every vector maps to a claimed property.

Chain under test (5 hops of authority, 4 delegations):
  principal(acme) → orchestrator → researcher → collector → summarizer
Scope narrows at each hop; the harness then attacks the chain 14 ways.
Run: python -m pytest tests/ -q
"""
from __future__ import annotations

import json
import statistics
import time

import pytest

from olinool import (
    Decision,
    KeyResolver,
    MintError,
    Policy,
    Signer,
    attenuate,
    invoke,
    mint_root,
    verify_chain,
    verify_invocation,
)
from olinool.core import b64u_decode, b64u_encode, canonical_json
from olinool.errors import (
    ERR_ASSURANCE,
    ERR_AUDIENCE,
    ERR_DEPTH,
    ERR_EXPIRED,
    ERR_LINKAGE,
    ERR_PARENT_HASH,
    ERR_POP,
    ERR_REPLAY,
    ERR_REVOKED_EPOCH,
    ERR_SCOPE_WIDENED,
    ERR_SIG,
    ERR_STRUCTURE,
    ERR_ROOT_UNTRUSTED,
)

NOW = int(time.time())
REQ = b'{"method":"GET","path":"/datasets/eu-42"}'
RECEIVER = "did:web:data.example"


def resign(jws: str, signer: Signer, mutate) -> str:
    """Decode payload, apply mutate(payload), re-sign with `signer`."""
    h_b, p_b, _ = jws.split(".")
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    mutate(payload)
    header["kid"] = payload["iss"]
    h2 = b64u_encode(canonical_json(header))
    p2 = b64u_encode(canonical_json(payload))
    sig = b64u_encode(signer.sign(f"{h2}.{p2}".encode()))
    return f"{h2}.{p2}.{sig}"


def tamper_without_resign(jws: str, mutate) -> str:
    h_b, p_b, s_b = jws.split(".")
    payload = json.loads(b64u_decode(p_b))
    mutate(payload)
    return f"{h_b}.{b64u_encode(canonical_json(payload))}.{s_b}"


@pytest.fixture(scope="module")
def world():
    principal = Signer.generate("did:web:acme.example")
    orch = Signer.generate("did:web:acme.example:orchestrator")
    research = Signer.generate("did:web:acme.example:researcher")
    collect = Signer.generate("did:web:vendor.example:collector")
    summar = Signer.generate("did:web:vendor.example:summarizer")
    attacker = Signer.generate("did:web:evil.example:mallory")

    resolver = KeyResolver()
    for s in (principal, orch, research, collect, summar, attacker):
        resolver.register_signer(s)

    r0 = mint_root(
        principal,
        orch.agent_id,
        scope=[
            {"act": "read", "res": "datasets/*", "limits": {"amount": 50}},
            {"act": "write", "res": "reports/*"},
        ],
        ttl_s=3600,
        max_depth=4,
        now=NOW,
    )
    r1 = attenuate(
        r0, orch, research.agent_id,
        scope=[
            {"act": "read", "res": "datasets/*", "limits": {"amount": 25}},
            {"act": "write", "res": "reports/q3/*"},
        ],
        now=NOW,
    )
    r2 = attenuate(
        r1, research, collect.agent_id,
        scope=[{"act": "read", "res": "datasets/eu-*", "limits": {"amount": 10}}],
        now=NOW,
    )
    r3 = attenuate(
        r2, collect, summar.agent_id,
        scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}],
        audience=[RECEIVER],
        now=NOW,
    )
    chain = [r0, r1, r2, r3]
    return dict(
        principal=principal, orch=orch, research=research, collect=collect,
        summar=summar, attacker=attacker, resolver=resolver, chain=chain,
    )


def fresh_policy(**kw) -> Policy:
    return Policy(**kw)


# ---------------------------------------------------------------- happy path

def test_c01_happy_path_full_chain(world):
    inv = invoke(world["chain"][-1], world["summar"], RECEIVER, REQ, now=NOW)
    d = verify_invocation(world["chain"], inv, REQ, RECEIVER, world["resolver"], fresh_policy(), now=NOW)
    assert d.allowed, d
    assert d.effective_scope == [{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 5}}]


# ------------------------------------------------------- attenuation attacks

def test_c02_mint_guard_rejects_widening(world):
    with pytest.raises(MintError):
        attenuate(world["chain"][2], world["collect"], world["summar"].agent_id,
                  scope=[{"act": "write", "res": "reports/*"}], now=NOW)


def test_c03_forged_widened_hop_rejected_by_verifier(world):
    # Malicious minter skips guards and signs a widened child itself.
    widened = resign(
        world["chain"][3], world["collect"],
        lambda p: p.update(scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 500}}]),
    )
    d = verify_chain(world["chain"][:3] + [widened], world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_SCOPE_WIDENED


def test_c04_limit_key_dropped_is_widening(world):
    # Dropping the parent's {"amount": ...} ceiling = unbounded = widened.
    no_limit = resign(
        world["chain"][3], world["collect"],
        lambda p: p.update(scope=[{"act": "read", "res": "datasets/eu-42"}]),
    )
    d = verify_chain(world["chain"][:3] + [no_limit], world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_SCOPE_WIDENED


# --------------------------------------------------------- linkage / splicing

def test_c05_hop_minted_by_non_subject(world):
    # Attacker signs a "child" of r2 naming itself issuer — continuity breaks.
    rogue = resign(
        world["chain"][3], world["attacker"],
        lambda p: p.update(iss=world["attacker"].agent_id),
    )
    d = verify_chain(world["chain"][:3] + [rogue], world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_LINKAGE


def test_c06_parent_hash_splice(world):
    # Graft r3 onto a different (freshly minted, valid-looking) parent bytes.
    alt_r2 = attenuate(
        world["chain"][1], world["research"], world["collect"].agent_id,
        scope=[{"act": "read", "res": "datasets/eu-*", "limits": {"amount": 10}}],
        now=NOW,
    )
    d = verify_chain([world["chain"][0], world["chain"][1], alt_r2, world["chain"][3]],
                     world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_PARENT_HASH


def test_c07_tampered_payload_signature_fails(world):
    tampered = tamper_without_resign(world["chain"][2], lambda p: p["scope"][0].update({"res": "datasets/*"}))
    d = verify_chain(world["chain"][:2] + [tampered, world["chain"][3]],
                     world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error in (ERR_SIG, ERR_PARENT_HASH)  # sig breaks first


def test_c08_fake_root_untrusted_principal(world):
    fake_root = mint_root(world["attacker"], world["orch"].agent_id,
                          scope=[{"act": "read", "res": "datasets/*"}], now=NOW)
    pol = fresh_policy(trusted_principals={"did:web:acme.example"})
    d = verify_chain([fake_root], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_ROOT_UNTRUSTED


# ------------------------------------------------------------- time and depth

def test_c09_expired_leaf(world):
    d = verify_chain(world["chain"], world["resolver"], fresh_policy(), now=NOW + 7200)
    assert not d.allowed and d.error == ERR_EXPIRED


def test_c10_depth_exhausted(world):
    r4 = attenuate(world["chain"][3], world["summar"], world["attacker"].agent_id,
                   scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 1}}], now=NOW)
    # r3 was minted with parent_remaining=... => r4 legal only if depth remains.
    # Chain r0(max_depth=4) → 4 delegations = at the limit; a 5th must fail at mint.
    with pytest.raises(MintError):
        attenuate(r4, world["attacker"], "did:web:evil.example:deeper",
                  scope=[{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 1}}], now=NOW)


def test_c10b_forged_depth_extension_caught_by_verifier(world):
    # Leaf re-signs its own receipt claiming max_depth=9, then delegates on.
    # Root's declared budget still caps the chain at the verifier (R8).
    inflated = resign(world["chain"][3], world["collect"],
                      lambda p: p["cst"].update(max_depth=9))
    narrow = [{"act": "read", "res": "datasets/eu-42", "limits": {"amount": 1}}]
    r4 = attenuate(inflated, world["summar"], world["attacker"].agent_id, scope=narrow, now=NOW)
    r5 = attenuate(r4, world["attacker"], "did:web:evil.example:deeper", scope=narrow, now=NOW)
    # Colluding minters accepted 5 delegations; root only authorized 4.
    d = verify_chain(world["chain"][:3] + [inflated, r4, r5], world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_DEPTH


# ------------------------------------------------- possession / replay / aud

def test_c11_stolen_chain_wrong_invoker(world):
    # Attacker observed the whole chain but does not hold the leaf subject key.
    inv = invoke(world["chain"][-1], world["attacker"], RECEIVER, REQ, now=NOW)
    d = verify_invocation(world["chain"], inv, REQ, RECEIVER, world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_POP


def test_c12_truncated_chain_presented_by_descendant(world):
    # Summarizer presents ancestors' broader hop (r1) to escape its narrow scope.
    inv = invoke(world["chain"][1], world["summar"], RECEIVER, REQ, now=NOW)
    d = verify_invocation(world["chain"][:2], inv, REQ, RECEIVER, world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_POP  # invocation signer ≠ that hop's subject


def test_c13_invocation_replay(world):
    pol = fresh_policy()
    inv = invoke(world["chain"][-1], world["summar"], RECEIVER, REQ, now=NOW)
    first = verify_invocation(world["chain"], inv, REQ, RECEIVER, world["resolver"], pol, now=NOW)
    second = verify_invocation(world["chain"], inv, REQ, RECEIVER, world["resolver"], pol, now=NOW)
    assert first.allowed and not second.allowed and second.error == ERR_REPLAY


def test_c14_wrong_audience(world):
    other = "did:web:other-api.example"
    inv = invoke(world["chain"][-1], world["summar"], other, REQ, now=NOW)
    d = verify_invocation(world["chain"], inv, REQ, other, world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_AUDIENCE  # leaf aud pins RECEIVER


def test_c15_request_binding(world):
    inv = invoke(world["chain"][-1], world["summar"], RECEIVER, REQ, now=NOW)
    other_req = b'{"method":"DELETE","path":"/datasets/eu-42"}'
    d = verify_invocation(world["chain"], inv, other_req, RECEIVER, world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_POP


# ------------------------------------------------------- policy dimensions

def test_c16_revocation_epoch(world):
    pol = fresh_policy(current_epoch=lambda issuer: 3 if issuer == "did:web:acme.example" else None)
    d = verify_chain(world["chain"], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_REVOKED_EPOCH


def test_c17_assurance_floor(world):
    pol = fresh_policy(min_assurance=1)
    d = verify_chain(world["chain"], world["resolver"], pol, now=NOW)
    assert not d.allowed and d.error == ERR_ASSURANCE  # L0 chain, L1 required


def test_c19_single_agent_chain_length_one(world):
    # Single-agent mode: principal -> agent, no delegation. The moolam alone
    # + possession is a complete authorization artifact for tool calls.
    solo = Signer.generate("did:web:acme.example:solo")
    world["resolver"].register_signer(solo)
    r0 = mint_root(world["principal"], solo.agent_id,
                   scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 5}}],
                   ttl_s=600, max_depth=0, now=NOW)
    inv = invoke(r0, solo, RECEIVER, REQ, now=NOW)
    d = verify_invocation([r0], inv, REQ, RECEIVER, world["resolver"], fresh_policy(), now=NOW)
    assert d.allowed
    # and with max_depth=0 the solo agent cannot delegate onward at all
    with pytest.raises(MintError):
        attenuate(r0, solo, world["attacker"].agent_id,
                  scope=[{"act": "read", "res": "datasets/x", "limits": {"amount": 1}}], now=NOW)


def test_c20_alg_confusion_rejected(world):
    # Classic JWT-class attack: swap the header alg (downgrade/none attack).
    # Single-algorithm policy (EdDSA only, no negotiation) must reject at the
    # structure stage. This is what makes a future PQC migration (ML-DSA) a
    # clean version bump instead of a negotiable — and downgradable — option.
    h_b, p_b, s_b = world["chain"][0].split(".")
    header = json.loads(b64u_decode(h_b))
    header["alg"] = "HS256"
    forged = f"{b64u_encode(canonical_json(header))}.{p_b}.{s_b}"
    d = verify_chain([forged] + world["chain"][1:], world["resolver"], fresh_policy(), now=NOW)
    assert not d.allowed and d.error == ERR_STRUCTURE


# ------------------------------------------------------------------ latency

def test_c18_l0_verify_latency_budget(world):
    pol = fresh_policy()
    samples = []
    for _ in range(200):
        t0 = time.perf_counter()
        d = verify_chain(world["chain"], world["resolver"], pol, now=NOW)
        samples.append((time.perf_counter() - t0) * 1000)
        assert d.allowed
    median = statistics.median(samples)
    print(f"\n  L0 verify, 4-delegation chain: median {median:.3f} ms "
          f"(p95 {sorted(samples)[189]:.3f} ms)")
    assert median < 5.0, "offline L0 verification must stay in single-digit ms"
