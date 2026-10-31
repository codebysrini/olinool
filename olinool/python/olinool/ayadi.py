"""olinool.ayadi — the offline chain + invocation verifier (spec §5–§6).

This is the module that ships first. Zero network calls: the KeyResolver is
injected, the clock is injectable, revocation epoch lookup is an optional
callback. Every rule maps to a numbered spec rule R1–R12 and a closed error
code, so conformance vectors can assert exact failures.
"""
from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from .core import sha256_b64u
from .errors import (
    ERR_ASSURANCE,
    ERR_AUDIENCE,
    ERR_DEPTH,
    ERR_EXPIRED,
    ERR_LINKAGE,
    ERR_PARENT_HASH,
    ERR_POP,
    ERR_PROFILE_MIXED,
    ERR_PROFILE_NOT_ALLOWED,
    ERR_REPLAY,
    ERR_REVOKED_EPOCH,
    ERR_ROOT_UNTRUSTED,
    ERR_SCOPE_WIDENED,
    ERR_SIG,
    ERR_STRUCTURE,
    ERR_TIME_NOT_NESTED,
    Decision,
)
from .keys import KeyResolver
from .muthirai import VERSION  # noqa: F401  (kept for claim-schema version check)
from .profiles import ProfileParseError, decode_artifact, envelope_of, get_profile, select_profile
from .scopes import ScopeError, is_subset, validate_scope

_REQUIRED_CLAIMS = {"v", "rid", "prh", "pri", "iss", "sub", "scope", "cst", "asr"}


@dataclass
class Policy:
    """Receiver-side verification policy."""

    clock_skew_s: int = 60
    invocation_ttl_s: int = 120
    min_assurance: int = 0
    max_chain_len: int = 16
    trusted_principals: Optional[Set[str]] = None  # None => any resolvable principal
    current_epoch: Optional[Callable[[str], Optional[int]]] = None
    replay_cache: Set[str] = field(default_factory=set)  # in-proc; distributed cache is deployment concern
    allowed_profiles: Set[str] = field(default_factory=lambda: {"jws-1"})  # encoding allow-list (design §5)


def _check_receipt_structure(payload: Dict[str, Any]) -> Optional[str]:
    missing = _REQUIRED_CLAIMS - payload.keys()
    if missing:
        return f"missing claims: {sorted(missing)}"
    if payload["v"] != VERSION:
        return f"unsupported version {payload['v']!r}"
    cst = payload["cst"]
    if not isinstance(cst, dict):
        return "cst must be an object"
    for k in ("iat", "exp", "max_depth", "epoch"):
        if not isinstance(cst.get(k), int):
            return f"cst.{k} must be an integer"
    asr = payload["asr"]
    if not isinstance(asr, dict) or asr.get("level") not in (0, 1, 2):
        return "asr.level must be 0, 1, or 2"
    if "aud" in payload and (
        not isinstance(payload["aud"], list) or not all(isinstance(a, str) for a in payload["aud"])
    ):
        return "aud must be a list of strings"
    try:
        validate_scope(payload["scope"])
    except ScopeError as e:
        return f"scope: {e}"
    return None


def verify_chain(
    chain: List[str],
    resolver: KeyResolver,
    policy: Optional[Policy] = None,
    now: Optional[int] = None,
) -> Decision:
    """R1–R10: verify a Receipt chain root→leaf. No invocation binding yet.

    Structure: per hop the profile codec owns R1 (envelope) + R2 (signature);
    profile SELECTION (marker + allow-list, no negotiation) sits between the
    envelope parse and the claim-schema check, exactly where the old typ check
    was. All hops must share one profile (§5). R3–R10 then run on decoded
    claims via `verify_chain_claims` — encoding-agnostic, moved not rewritten.
    """
    policy = policy or Policy()
    t_now = int(now if now is not None else time.time())

    if not chain or len(chain) > policy.max_chain_len:
        return Decision.deny(ERR_STRUCTURE, "empty chain or chain too long")

    decoded: List[Dict[str, Any]] = []
    raw: List[str] = []
    profile_ids: List[str] = []
    for idx, jws in enumerate(chain):
        # R1a envelope (family codec via structural sniff): compact-JWS parse or
        # SD-JWT combined-form parse + disclosure-digest resolution (§16.2), each
        # with alg==EdDSA. Malformed / non-EdDSA / bad disclosure -> ERR_STRUCTURE
        # (c20 alg-confusion unchanged).
        try:
            dec = decode_artifact(jws)
        except ProfileParseError as e:
            return Decision.deny(ERR_STRUCTURE, f"hop {idx}: {e}")
        # Profile selection by the artifact's own markers (typ, v) within its
        # structural envelope family, gated by the policy allow-list. Unknown/
        # disallowed profile -> reject before claim logic (design §5).
        pid = select_profile(dec.header, dec.claims, policy.allowed_profiles, envelope=envelope_of(jws))
        if pid is None:
            return Decision.deny(ERR_PROFILE_NOT_ALLOWED, f"hop {idx}: profile not in allow-list")
        # R1b claim schema (data model, profile-agnostic).
        err = _check_receipt_structure(dec.claims)
        if err:
            return Decision.deny(ERR_STRUCTURE, f"hop {idx}: {err}")
        # R2 signature by claimed issuer (profile envelope).
        if dec.header.get("kid") != dec.claims["iss"] or not get_profile(pid).verify_sig(
            dec, resolver, dec.claims["iss"]
        ):
            return Decision.deny(ERR_SIG, f"hop {idx}: signature invalid for issuer {dec.claims['iss']!r}")
        decoded.append(dec.claims)
        # R5 preimage seam (SPEC §16.4): carry the PROFILE-decoded artifact_bytes,
        # not the verbatim wire string. For jws-1 they are identical by definition
        # (golden-bytes + frozen-corpus gate); for sd-1 this is the issuer-signed
        # base, so a parent's hash is stable across holder-selected disclosures.
        raw.append(dec.artifact_bytes)
        profile_ids.append(pid)

    # Uniform-profile rule (§5): all hops must share one profile.
    if len(set(profile_ids)) > 1:
        return Decision.deny(ERR_PROFILE_MIXED, f"chain mixes profiles: {sorted(set(profile_ids))}")

    return verify_chain_claims(decoded, raw, resolver, policy, t_now)


def verify_chain_claims(
    decoded: List[Dict[str, Any]],
    raw: List[str],
    resolver: KeyResolver,
    policy: Policy,
    t_now: int,
) -> Decision:
    """R3–R10 — the encoding-agnostic data model. Operates only on decoded claim
    dicts + the profile-provided artifact_bytes strings (`raw` — the R5
    parent-hash preimages, SPEC §16.4; for jws-1 the verbatim wire strings).
    Moved verbatim from the pre-v0.3 `verify_chain` body; no rule logic changed.
    `resolver` is kept for interface stability (L1+ assurance-evidence checking
    is reserved)."""
    root = decoded[0]
    # R3 root anchoring
    if root["prh"] is not None or root["iss"] != root["pri"]:
        return Decision.deny(ERR_ROOT_UNTRUSTED, "root must have prh=null and iss==pri")
    if policy.trusted_principals is not None and root["pri"] not in policy.trusted_principals:
        return Decision.deny(ERR_ROOT_UNTRUSTED, f"principal {root['pri']!r} not trusted by policy")

    n = len(decoded)
    for i in range(1, n):
        cur, prev = decoded[i], decoded[i - 1]
        # R4 issuer/subject continuity + stable principal
        if cur["iss"] != prev["sub"] or cur["pri"] != root["pri"]:
            return Decision.deny(ERR_LINKAGE, f"hop {i}: issuer/principal continuity violated")
        # R5 parent hash binds exact bytes
        if cur["prh"] != sha256_b64u(raw[i - 1].encode("ascii")):
            return Decision.deny(ERR_PARENT_HASH, f"hop {i}: prh does not match parent receipt")
        # R6 monotonic scope attenuation
        try:
            if not is_subset(cur["scope"], prev["scope"]):
                return Decision.deny(ERR_SCOPE_WIDENED, f"hop {i}: scope not ⊆ parent scope")
        except ScopeError as e:
            return Decision.deny(ERR_STRUCTURE, f"hop {i}: scope: {e}")
        # R7 time windows nest
        if cur["cst"]["iat"] < prev["cst"]["iat"] or cur["cst"]["exp"] > prev["cst"]["exp"]:
            return Decision.deny(ERR_TIME_NOT_NESTED, f"hop {i}: window not nested in parent")

    # R7b leaf window vs wall clock (nesting makes the leaf the tightest window)
    leaf = decoded[-1]
    if t_now > leaf["cst"]["exp"] + policy.clock_skew_s:
        return Decision.deny(ERR_EXPIRED, "leaf receipt expired")
    if t_now < leaf["cst"]["iat"] - policy.clock_skew_s:
        return Decision.deny(ERR_EXPIRED, "leaf receipt not yet valid")

    # R8 depth: hops after i must not exceed hop i's declared max_depth
    for i in range(n):
        if (n - 1 - i) > decoded[i]["cst"]["max_depth"]:
            return Decision.deny(ERR_DEPTH, f"hop {i} allows {decoded[i]['cst']['max_depth']} further hops")

    # R9 revocation epoch (optional online-ish signal; offline => TTL bounds risk)
    if policy.current_epoch is not None:
        for i, p in enumerate(decoded):
            required = policy.current_epoch(p["iss"])
            if required is not None and p["cst"]["epoch"] < required:
                return Decision.deny(ERR_REVOKED_EPOCH, f"hop {i}: epoch {p['cst']['epoch']} < {required}")

    # R10 assurance: chain level = min over hops; evidence checking is L1+ (reserved)
    chain_level = min(p["asr"]["level"] for p in decoded)
    if chain_level < policy.min_assurance:
        return Decision.deny(ERR_ASSURANCE, f"chain assurance L{chain_level} < required L{policy.min_assurance}")

    return Decision.allow(effective_scope=leaf["scope"])


def verify_invocation(
    chain: List[str],
    invocation_jws: str,
    request_bytes: bytes,
    receiver_id: str,
    resolver: KeyResolver,
    policy: Optional[Policy] = None,
    now: Optional[int] = None,
) -> Decision:
    """R1–R12: full receiver-side check for one concrete request."""
    policy = policy or Policy()
    t_now = int(now if now is not None else time.time())

    chain_decision = verify_chain(chain, resolver, policy, now=t_now)
    if not chain_decision.allowed:
        return chain_decision
    # The chain is uniform-profile (verify_chain enforced §5); the leaf's profile
    # is the chain's profile.
    leaf_dec = decode_artifact(chain[-1])
    leaf = leaf_dec.claims
    chain_profile = select_profile(
        leaf_dec.header, leaf_dec.claims, policy.allowed_profiles, envelope=envelope_of(chain[-1])
    )

    # R11 audience
    if "aud" in leaf and not any(fnmatch.fnmatchcase(receiver_id, pat) for pat in leaf["aud"]):
        return Decision.deny(ERR_AUDIENCE, f"receiver {receiver_id!r} not in leaf aud")

    # R12 proof of possession — envelope via the profile codec (parse / non-EdDSA
    # -> ERR_POP, as before), then the invocation MUST be the chain's profile (§5).
    try:
        inv_dec = decode_artifact(invocation_jws)
    except ProfileParseError as e:
        return Decision.deny(ERR_POP, f"invocation: {e}")
    inv_profile = select_profile(
        inv_dec.header, inv_dec.claims, policy.allowed_profiles, envelope=envelope_of(invocation_jws)
    )
    if inv_profile is None:
        return Decision.deny(ERR_PROFILE_NOT_ALLOWED, "invocation profile not in allow-list")
    if inv_profile != chain_profile:
        return Decision.deny(ERR_PROFILE_MIXED, "invocation profile differs from chain profile")
    header, inv, signing_input, sig = inv_dec.header, inv_dec.claims, inv_dec.signing_input, inv_dec.sig
    if inv.get("aud") != receiver_id:
        return Decision.deny(ERR_AUDIENCE, "invocation aud mismatch")
    # Leaf-binding preimage (SPEC §16.4): rcp binds the profile's artifact_bytes
    # — for jws-1 the verbatim leaf wire string (identical to pre-sd-1 behavior),
    # for sd-1 the issuer-signed base, stable across holder-selected disclosures.
    if inv.get("rcp") != sha256_b64u(leaf_dec.artifact_bytes.encode("ascii")):
        return Decision.deny(ERR_POP, "invocation not bound to presented leaf receipt")
    if inv.get("req") != sha256_b64u(request_bytes):
        return Decision.deny(ERR_POP, "invocation not bound to this request")
    if inv.get("sub") != leaf["sub"] or header.get("kid") != leaf["sub"]:
        return Decision.deny(ERR_POP, "invocation signer is not the leaf subject")
    if not resolver.verify(leaf["sub"], signing_input, sig):
        return Decision.deny(ERR_POP, "invocation signature invalid")
    iat = inv.get("iat")
    if not isinstance(iat, int) or abs(t_now - iat) > policy.invocation_ttl_s + policy.clock_skew_s:
        return Decision.deny(ERR_POP, "invocation outside freshness window")
    nonce = inv.get("nnc")
    if not isinstance(nonce, str) or not nonce:
        return Decision.deny(ERR_POP, "invocation nonce missing")
    cache_key = f"{leaf['sub']}:{nonce}"
    if cache_key in policy.replay_cache:
        return Decision.deny(ERR_REPLAY, "invocation nonce replayed")
    policy.replay_cache.add(cache_key)

    return Decision.allow(effective_scope=leaf["scope"])
