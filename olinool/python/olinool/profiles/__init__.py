"""olinool.profiles — the encoding/profile seam (design §2–§5).

A *profile* owns the per-encoding codec (R1 envelope parse + R2 signature +
mint-side serialize/canonicalize). The DATA MODEL (R3–R12 claim logic, scope
algebra, closed error set) is profile-agnostic and lives in `ayadi`/`scopes`/
`errors`.

Selection is by the artifact's OWN markers via each profile's `matches`
predicate — NEVER by peer negotiation. A `Policy` carries an allow-list
(default `{"jws-1"}`); an artifact whose profile is not allowed is rejected
with `ERR_PROFILE_NOT_ALLOWED` before any claim logic. This is the c20
no-downgrade doctrine generalized from algorithms to whole encodings: one
profile per artifact, acceptance by policy, downgrade structurally impossible.

Two profiles ship: `jws-1` (compact JWS, the frozen v0.1 wire) and `sd-1`
(SD-JWT combined form, SPEC §16). They live in different structural ENVELOPE
FAMILIES, told apart by the sniff this module's first version reserved: the
SD-JWT combined form is `~`-delimited, and `~` can never appear in a compact
JWS (base64url alphabet + '.'). The sniff picks the family CODEC
(`decode_artifact`); marker selection (`select_profile`) is then constrained
to profiles of the same family, so a plain JWS re-tagged with another family's
typ markers can never select that family's profile (the structure half of the
REGISTRY.md predicates).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Set

from .jws1 import JWS1_PROFILE, Decoded, ProfileParseError  # noqa: F401 re-export
from .sd1 import SD1_PROFILE  # noqa: F401 re-export

# Structural envelope families (see module docstring).
ENVELOPE_JWS = "jws"        # compact JWS — no '~' possible
ENVELOPE_SD_JWT = "sd-jwt"  # SD-JWT combined form — '~'-delimited (SPEC §16.1)

_REGISTRY: Dict[str, Any] = {}


def register(profile: Any) -> None:
    """Register a profile by its stable id. Used at import time for jws-1 and
    by tests to install throwaway stub profiles."""
    _REGISTRY[profile.id] = profile


def unregister(profile_id: str) -> None:
    _REGISTRY.pop(profile_id, None)


def get_profile(profile_id: str) -> Optional[Any]:
    return _REGISTRY.get(profile_id)


def registered_ids() -> Set[str]:
    return set(_REGISTRY)


def envelope_of(artifact: str) -> str:
    """Structural sniff (module docstring): which envelope family carries this
    artifact. Purely structural — reads no claims, negotiates nothing."""
    return ENVELOPE_SD_JWT if "~" in artifact else ENVELOPE_JWS


def decode_artifact(artifact: str) -> Decoded:
    """Family-codec dispatch: sniff the structural envelope, decode with that
    family's codec. All compact-JWS profiles share the jws-1 envelope parse;
    the SD-JWT family's codec is sd-1. Raises ProfileParseError on any
    envelope failure (the caller maps it to the slot's structural code)."""
    if envelope_of(artifact) == ENVELOPE_SD_JWT:
        prof = _REGISTRY.get("sd-1")
        if prof is None:
            raise ProfileParseError("no codec registered for the SD-JWT combined form")
        return prof.decode(artifact)
    return JWS1_PROFILE.decode(artifact)


def select_profile(
    header: Dict[str, Any],
    claims: Dict[str, Any],
    allowed: Set[str],
    envelope: str = ENVELOPE_JWS,
) -> Optional[str]:
    """Return the artifact's profile id, gated by the allow-list.

    A profile is selected only when it is allowed, its structural envelope
    family matches the artifact's (default compact-JWS; profiles declare
    `envelope`, absent = jws), AND its marker predicate matches. Returns None
    otherwise — whether because the matching profile is not allowed, or
    because no profile matches at all. The caller maps None to
    ERR_PROFILE_NOT_ALLOWED. Never negotiates with a peer (instinct 9)."""
    for pid, prof in _REGISTRY.items():
        if (
            pid in allowed
            and getattr(prof, "envelope", ENVELOPE_JWS) == envelope
            and prof.matches(header, claims)
        ):
            return pid
    return None


register(JWS1_PROFILE)
register(SD1_PROFILE)
