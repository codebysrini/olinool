"""olinool.profiles.jws1 — the jws-1 profile: the v0.1 compact-JWS codec.

`jws-1` ≡ the v0.1 wire format, now named (design §4): compact JWS,
`alg:"EdDSA"`, `typ` ∈ {olinool-receipt+jws, olinool-invocation+jws,
olinool-result+jws}, receipt/result payload `v:"0.1"`, RFC-8785 (JCS)
canonicalization, Ed25519. It is FROZEN: once released its bytes and verdicts
never change; fixes ship as a NEW profile id, never as a mutation.

This module is CARRIAGE extracted verbatim from `moolam.jws` + the R1/R2 block
of `ayadi` — same bytes, same signing_input, same signature decision. No claim
logic (R3–R12) lives here: that stays encoding-agnostic in the data model
(`ayadi`). The boundary is exactly the one the design (§2) relies on.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from moolam.core import canonical_json
from moolam.jws import jws_decode as _jws_decode
from moolam.jws import jws_sign as _jws_sign
from moolam.keys import KeyResolver, Signer

RECEIPT_TYP = "olinool-receipt+jws"
INVOCATION_TYP = "olinool-invocation+jws"
RESULT_TYP = "olinool-result+jws"
VERSION = "0.1"


class ProfileParseError(Exception):
    """Envelope-level structural failure (compact-JWS parse or non-EdDSA alg).

    The caller maps this to the slot's structural code: ERR_STRUCTURE for a
    receipt slot, ERR_POP for an invocation slot — matching pre-refactor
    behavior exactly.
    """


@dataclass
class Decoded:
    header: Dict[str, Any]
    claims: Dict[str, Any]
    signing_input: bytes
    sig: bytes
    # The profile-defined R5 parent-hash preimage (SPEC §16.4). For jws-1 this is
    # the VERBATIM received string; for sd-1 it will be the issuer-signed base
    # (the JWT before holder-selected disclosures).
    artifact_bytes: str


class _Jws1Profile:
    """Reference profile: equals today's behavior exactly."""

    id = "jws-1"
    receipt_typ = RECEIPT_TYP
    invocation_typ = INVOCATION_TYP
    result_typ = RESULT_TYP
    version = VERSION
    # Structural envelope family (registry metadata for codec dispatch and
    # family-gated selection — NOT a wire change; jws-1 bytes stay frozen).
    envelope = "jws"

    def decode(self, artifact: str) -> Decoded:
        """R1a envelope: compact-JWS parse + `alg==EdDSA`. Never checks typ/v
        (those are the selection predicate, §5). For jws-1, `artifact_bytes`
        — the profile's R5 parent-hash preimage — IS the exact received
        string, hashed verbatim; the verifier never re-serializes to compute
        a parent hash."""
        try:
            header, claims, signing_input, sig = _jws_decode(artifact)
        except Exception as e:  # noqa: BLE001 — any parse failure is structural
            raise ProfileParseError(str(e)) from e
        if header.get("alg") != "EdDSA":
            raise ProfileParseError("alg must be EdDSA (single-algorithm policy)")
        return Decoded(header, claims, signing_input, sig, artifact)

    def matches(self, header: Dict[str, Any], claims: Dict[str, Any]) -> bool:
        """The selection predicate (design §5, ratified): `(typ, v)` for
        receipts and results; `typ` alone for invocations (they carry no
        version claim)."""
        typ = header.get("typ")
        if typ == self.receipt_typ or typ == self.result_typ:
            return claims.get("v") == self.version
        if typ == self.invocation_typ:
            return True
        return False

    def verify_sig(self, decoded: Decoded, resolver: KeyResolver, agent_id: str) -> bool:
        """R2 envelope signature over the signing input."""
        return resolver.verify(agent_id, decoded.signing_input, decoded.sig)

    def serialize(self, signer: Signer, typ: str, claims: Dict[str, Any]) -> str:
        """Mint-side: press the seal. Byte-identical to the pre-refactor
        `moolam.jws.jws_sign` it delegates to (proven by the golden oracle)."""
        return _jws_sign(signer, typ, claims)

    def canonicalize(self, obj: Dict[str, Any]) -> bytes:
        """RFC-8785 JCS, for hashing/signing preimages."""
        return canonical_json(obj)


JWS1_PROFILE = _Jws1Profile()
