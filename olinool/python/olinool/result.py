"""olinool.result — signed outcome records: the action half of the audit.

A Receipt chain proves who was ALLOWED to act (authority); a Result record
is the acting agent's signed statement of what was DONE, hash-linked to the
exact leaf receipt it exercised and optionally to the invocation that
carried the request. Cross-linked, they are the two halves of an auditable
delegation (spec §14). Formalizes the format dabba's bridge stub previously
emitted as an unsigned dict.

Wire form: compact JWS, header {"alg":"EdDSA","typ":"olinool-result+jws",
"kid":"<acting agent id>"}. Payload:
  v       "0.1"
  typ     "olinool-result"
  rid     result id (uuid4)
  rcp     b64u sha256 of the leaf receipt JWS this attests to
  inv     b64u sha256 of the invocation JWS | null
  sub     acting agent id — MUST equal the leaf receipt's sub
  status  "completed" | "failed" | "partial"
  out     b64u sha256 of the output bytes
  ver     "self" | "counter" | "attested"   (verification level)
  iat     unix seconds

Results are archival artifacts, not credentials: verification checks
structure, signature, and binding — no freshness window, no replay cache.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional, Set

from .core import sha256_b64u
from .errors import (
    ERR_PROFILE_MIXED,
    ERR_PROFILE_NOT_ALLOWED,
    ERR_RESULT_BINDING,
    ERR_RESULT_SIG,
    ERR_RESULT_STRUCTURE,
    Decision,
    MintError,
)
from .keys import KeyResolver, Signer
from .muthirai import VERSION, jws_decode, receipt_hash
from .profiles import select_profile
from .profiles.jws1 import JWS1_PROFILE

RESULT_TYP = "olinool-result+jws"
RESULT_STATUSES = ("completed", "failed", "partial")
RESULT_VERIFICATION_LEVELS = ("self", "counter", "attested")

_REQUIRED_RESULT_CLAIMS = {"v", "typ", "rid", "rcp", "inv", "sub", "status", "out", "ver", "iat"}


def mint_result(
    leaf_receipt_jws: str,
    actor: Signer,
    output_bytes: bytes,
    status: str = "completed",
    invocation_jws: Optional[str] = None,
    ver: str = "self",
    now: Optional[int] = None,
) -> str:
    """Press the acting agent's seal onto an outcome.

    Mint-time guards mirror what verify_result re-checks; a malicious minter
    can skip them, which is exactly why receivers re-verify everything.
    """
    if status not in RESULT_STATUSES:
        raise MintError(f"status must be one of {RESULT_STATUSES}, got {status!r}")
    if ver not in RESULT_VERIFICATION_LEVELS:
        raise MintError(f"ver must be one of {RESULT_VERIFICATION_LEVELS}, got {ver!r}")
    _, leaf, _, _ = jws_decode(leaf_receipt_jws)
    if actor.agent_id != leaf["sub"]:
        raise MintError(f"actor {actor.agent_id!r} is not the leaf subject {leaf['sub']!r}")
    payload: Dict[str, Any] = {
        "v": VERSION,
        "typ": "olinool-result",
        "rid": str(uuid.uuid4()),
        "rcp": receipt_hash(leaf_receipt_jws),
        "inv": sha256_b64u(invocation_jws.encode("ascii")) if invocation_jws is not None else None,
        "sub": actor.agent_id,
        "status": status,
        "out": sha256_b64u(output_bytes),
        "ver": ver,
        "iat": int(now if now is not None else time.time()),
    }
    return JWS1_PROFILE.serialize(actor, RESULT_TYP, payload)


def verify_result(
    result_jws: str,
    leaf_receipt_jws: str,
    resolver: KeyResolver,
    allowed_profiles: Optional[Set[str]] = None,
) -> Decision:
    """Structure → signature → binding; first failure wins (mirrors ayadi).

    v0.3: the result artifact and the leaf receipt it attests to MUST share one
    profile from the allow-list (default {"jws-1"}), enforced before the binding
    check (design §5 — result verification matches the chain's profile rule)."""
    allowed = allowed_profiles if allowed_profiles is not None else {"jws-1"}
    try:
        header, payload, signing_input, sig = jws_decode(result_jws)
    except Exception as e:  # noqa: BLE001 — any parse failure is structural
        return Decision.deny(ERR_RESULT_STRUCTURE, f"result parse: {e}")
    if header.get("alg") != "EdDSA" or header.get("typ") != RESULT_TYP:
        return Decision.deny(ERR_RESULT_STRUCTURE, "result: bad header")
    missing = _REQUIRED_RESULT_CLAIMS - payload.keys()
    if missing:
        return Decision.deny(ERR_RESULT_STRUCTURE, f"missing claims: {sorted(missing)}")
    if payload["v"] != VERSION or payload["typ"] != "olinool-result":
        return Decision.deny(ERR_RESULT_STRUCTURE, "unsupported version or typ")
    if payload["status"] not in RESULT_STATUSES:
        return Decision.deny(ERR_RESULT_STRUCTURE, f"bad status {payload['status']!r}")
    if payload["ver"] not in RESULT_VERIFICATION_LEVELS:
        return Decision.deny(ERR_RESULT_STRUCTURE, f"bad ver {payload['ver']!r}")
    if not isinstance(payload["iat"], int):
        return Decision.deny(ERR_RESULT_STRUCTURE, "iat must be an integer")
    for k in ("rid", "rcp", "sub", "out"):
        if not isinstance(payload[k], str) or not payload[k]:
            return Decision.deny(ERR_RESULT_STRUCTURE, f"{k} must be a non-empty string")
    if payload["inv"] is not None and not isinstance(payload["inv"], str):
        return Decision.deny(ERR_RESULT_STRUCTURE, "inv must be a string or null")

    if header.get("kid") != payload["sub"] or not resolver.verify(payload["sub"], signing_input, sig):
        return Decision.deny(ERR_RESULT_SIG, f"signature invalid for sub {payload['sub']!r}")

    try:
        leaf_header, leaf, _, _ = jws_decode(leaf_receipt_jws)
    except Exception as e:  # noqa: BLE001
        return Decision.deny(ERR_RESULT_STRUCTURE, f"leaf receipt parse: {e}")

    # Profile match (design §5): result and leaf must share one allowed profile,
    # checked before binding. For jws-1 inputs this always holds.
    result_profile = select_profile(header, payload, allowed)
    leaf_profile = select_profile(leaf_header, leaf, allowed)
    if result_profile is None or leaf_profile is None:
        return Decision.deny(ERR_PROFILE_NOT_ALLOWED, "result or leaf profile not in allow-list")
    if result_profile != leaf_profile:
        return Decision.deny(ERR_PROFILE_MIXED, "result profile differs from leaf profile")

    if payload["sub"] != leaf.get("sub"):
        return Decision.deny(ERR_RESULT_BINDING, "result signer is not the leaf subject")
    if payload["rcp"] != receipt_hash(leaf_receipt_jws):
        return Decision.deny(ERR_RESULT_BINDING, "result not bound to presented leaf receipt")

    return Decision(allowed=True)
