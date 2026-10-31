"""olinool.muthirai — mint, attenuate, and serialize Delegation Receipts.

Wire form: compact JWS  base64url(header) . base64url(payload) . base64url(sig)
Header:  {"alg": "EdDSA", "typ": "olinool-receipt+jws", "kid": "<issuer agent id>"}

Payload claims (spec §4):
  v      "0.1"
  rid    receipt id (uuid4)
  prh    parent receipt hash: b64u(sha256(parent JWS bytes)) — null at root
  pri    principal id: the root authority this chain acts on behalf of
  iss    id of the delegating agent (MUST equal parent.sub for non-root)
  sub    id of the delegate (the ONLY identity that may invoke on this hop)
  aud    optional list of receiver id patterns this hop may be presented to
  scope  scope algebra (olinool.scopes) — MUST be ⊆ parent.scope
  cst    {"iat": s, "exp": s, "max_depth": n, "epoch": n}
  asr    {"level": 0|1|2, "evidence": null}   # L1/L2 evidence format reserved (EAT)

Mint-time guards enforce what verifiers re-check; a malicious minter can
skip guards, which is exactly why receivers re-verify everything.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from .core import b64u_decode, b64u_encode, canonical_json, sha256_b64u
from .errors import MintError
from .keys import Signer
from .scopes import ScopeError, is_subset, validate_scope

RECEIPT_TYP = "olinool-receipt+jws"
VERSION = "0.1"


# Seal press is shared across the stack; olinool presses receipts, dabba presses tiers.
from moolam.jws import jws_decode  # noqa: E402,F401  (re-exported for callers)
from moolam.jws import jws_sign as _jws_sign  # noqa: E402,F401  (re-exported for callers)

# v0.3: mint through the profile codec (default jws-1). Byte-identical to the
# hardcoded _jws_sign it delegates to — proven by the golden-bytes oracle.
from .profiles import ProfileParseError, decode_artifact, envelope_of, get_profile, registered_ids, select_profile  # noqa: E402
from .profiles.jws1 import JWS1_PROFILE  # noqa: E402,F401  (kept for callers/tests)


def _profile_or_raise(profile_id: str):
    prof = get_profile(profile_id)
    if prof is None:
        raise MintError(f"unknown profile {profile_id!r} (registered: {sorted(registered_ids())})")
    return prof


def receipt_hash(jws: str) -> str:
    return sha256_b64u(jws.encode("ascii"))


def mint_root(
    principal: Signer,
    subject_id: str,
    scope: List[Dict[str, Any]],
    ttl_s: int = 3600,
    max_depth: int = 4,
    epoch: int = 0,
    audience: Optional[List[str]] = None,
    assurance_level: int = 0,
    now: Optional[int] = None,
    profile: str = "jws-1",
) -> str:
    """Mint the Vinkaru (root receipt): principal delegates to the first agent.

    `profile` selects the encoding codec (default jws-1 — all pre-sd-1 call
    sites mint byte-identical wire, proven by the golden-bytes oracle). Under
    "sd-1" the disclosable claims move into salted-hash disclosures (SPEC §16)."""
    validate_scope(scope)
    prof = _profile_or_raise(profile)
    iat = int(now if now is not None else time.time())
    payload: Dict[str, Any] = {
        "v": VERSION,
        "rid": str(uuid.uuid4()),
        "prh": None,
        "pri": principal.agent_id,
        "iss": principal.agent_id,
        "sub": subject_id,
        "scope": scope,
        "cst": {"iat": iat, "exp": iat + ttl_s, "max_depth": max_depth, "epoch": epoch},
        "asr": {"level": assurance_level, "evidence": None},
    }
    if audience is not None:
        payload["aud"] = audience
    return prof.serialize(principal, prof.receipt_typ, payload)


def attenuate(
    parent_jws: str,
    issuer: Signer,
    subject_id: str,
    scope: List[Dict[str, Any]],
    ttl_s: Optional[int] = None,
    max_depth: Optional[int] = None,
    epoch: Optional[int] = None,
    audience: Optional[List[str]] = None,
    assurance_level: Optional[int] = None,
    now: Optional[int] = None,
    profile: Optional[str] = None,
) -> str:
    """Delegate onward with a strictly-narrowed scope.

    Guards (all re-checked by verifiers — R4..R8, plus the §15 uniform-profile
    rule at mint time):
      * issuer must BE the parent's subject
      * scope ⊆ parent.scope
      * time window nested inside parent's
      * remaining depth decreases
      * child profile == parent profile (default: inherit the parent's)
    """
    try:
        parent_dec = decode_artifact(parent_jws)
    except ProfileParseError as e:
        raise MintError(f"parent receipt: {e}") from e
    parent = parent_dec.claims
    # §15 uniform-profile at mint: infer the parent's profile from its own
    # markers (all registered ids — minting has no receiver allow-list); the
    # child inherits it unless explicitly (and identically) named.
    parent_profile = select_profile(
        parent_dec.header, parent, registered_ids(), envelope=envelope_of(parent_jws)
    )
    if parent_profile is None:
        raise MintError("parent receipt matches no registered profile")
    child_profile = parent_profile if profile is None else profile
    if child_profile != parent_profile:
        raise MintError(
            f"child profile {child_profile!r} must match parent profile "
            f"{parent_profile!r} (§15 uniform-profile rule)"
        )
    prof = _profile_or_raise(child_profile)
    if issuer.agent_id != parent["sub"]:
        raise MintError(f"issuer {issuer.agent_id!r} is not parent.sub {parent['sub']!r}")
    try:
        if not is_subset(scope, parent["scope"]):
            raise MintError("requested scope is not a subset of parent scope")
    except ScopeError as e:
        raise MintError(f"scope grammar: {e}") from e

    iat = int(now if now is not None else time.time())
    p_iat, p_exp = parent["cst"]["iat"], parent["cst"]["exp"]
    exp = p_exp if ttl_s is None else min(iat + ttl_s, p_exp)
    if iat < p_iat or exp > p_exp:
        raise MintError("child time window must nest inside parent window")

    parent_remaining = parent["cst"]["max_depth"]
    if parent_remaining < 1:
        raise MintError("parent has no delegation depth remaining")
    child_depth = parent_remaining - 1 if max_depth is None else min(max_depth, parent_remaining - 1)

    payload: Dict[str, Any] = {
        "v": VERSION,
        "rid": str(uuid.uuid4()),
        # R5 preimage (SPEC §16.4): hash the parent's profile-defined
        # artifact_bytes — for jws-1 the verbatim wire string (identical to
        # pre-sd-1 receipt_hash(parent_jws)), for sd-1 the issuer-signed base,
        # stable across holder-selected disclosures.
        "prh": receipt_hash(parent_dec.artifact_bytes),
        "pri": parent["pri"],
        "iss": issuer.agent_id,
        "sub": subject_id,
        "scope": scope,
        "cst": {
            "iat": iat,
            "exp": exp,
            "max_depth": child_depth,
            "epoch": parent["cst"]["epoch"] if epoch is None else epoch,
        },
        "asr": {
            "level": parent["asr"]["level"] if assurance_level is None else assurance_level,
            "evidence": None,
        },
    }
    if audience is not None:
        payload["aud"] = audience
    return prof.serialize(issuer, prof.receipt_typ, payload)
