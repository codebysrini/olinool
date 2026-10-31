"""olinool.profiles.sd1 — the sd-1 profile: SD-JWT selective disclosure (SPEC §16).

`sd-1` is an ENCODING/disclosure-layer profile only (RFC 9901): the artifact is
an SD-JWT combined form `<issuer-signed JWT>~<Disclosure 1>~...~<Disclosure N>~`
whose issuer-signed JWT hides holder-selectable claims behind salted-hash
disclosures (`_sd` digest arrays, `_sd_alg` pinned to sha-256). Crypto is
unchanged — Ed25519, single-algorithm policy (SPEC §9b); the R1–R12 data model
and the closed error set are untouched. There is NO KB-JWT: possession stays
the olinool Invocation (R12), so the combined form always ends with `~`.

R5/leaf-binding preimage (SPEC §16.4): `artifact_bytes` is the ISSUER-SIGNED
BASE — the compact JWT before the first `~` — never the combined form, so a
parent's hash is stable across holder-selected disclosures.

Claim split (SPEC §16.3, enforced mint-side here):
  * disclosable  → `rid`, `asr.evidence` (nested disclosure), `ext` (when present)
  * mandatory-cleartext → everything an R-rule reads: iss/sub/scope/prh/cst
    window + v/pri/max_depth/epoch/asr.level — AND `aud` (design note below).

Design note (resolves a §16.3 internal contradiction, same family as the two
flagged 2026-07-07): the §16.3 text listed upstream `aud` as disclosable, but
§16.3's own criterion — "every claim a verification rule reads" — covers `aud`:
R11 reads the leaf's `aud` *conditionally* ("if present"), and leaf-ness is
positional, so a holder withholding an `aud` disclosure would make an
audience-restricted receipt look unrestricted — a WIDENING channel (hidden must
never equal absent). `aud` therefore stays cleartext at mint and is not part of
the disclosable set in this implementation. Every remaining disclosable claim
fails CLOSED when withheld: a missing `rid` fails R1b (`ERR_STRUCTURE`); a
withheld `asr.evidence`/`ext` is read by no rule.

Fail-closed decode (SPEC §16.2): unknown digest, duplicate digest, malformed
disclosure, claim-name collision, or a non-pinned `_sd_alg` → ProfileParseError
(the caller's slot-structural code, ERR_STRUCTURE / ERR_POP). No new error
codes — the §7 closed set is unchanged.
"""
from __future__ import annotations

import json
import secrets
from typing import Any, Dict, List, Set, Tuple

from moolam.core import b64u_decode, b64u_encode, canonical_json, sha256_b64u
from moolam.jws import jws_decode as _jws_decode
from moolam.jws import jws_sign as _jws_sign
from moolam.keys import KeyResolver, Signer

from .jws1 import Decoded, ProfileParseError

RECEIPT_TYP = "olinool-receipt+sd-jwt"
INVOCATION_TYP = "olinool-invocation+sd-jwt"
RESULT_TYP = "olinool-result+sd-jwt"
VERSION = "0.1"
SD_ALG = "sha-256"  # pinned (§16.1); any other value is structural failure (instinct 9)


def _new_disclosure(name: str, value: Any) -> str:
    """RFC 9901 disclosure: b64u(JSON [salt, claim_name, claim_value]) with a
    128-bit random salt. The presented STRING is what gets digested, so the
    JSON serialization form travels with the disclosure and needs no canon
    agreement between implementations (we mint JCS for determinism of form)."""
    salt = b64u_encode(secrets.token_bytes(16))
    return b64u_encode(canonical_json([salt, name, value]))


def _disclosure_digest(disclosure: str) -> str:
    return sha256_b64u(disclosure.encode("ascii"))


def _parse_disclosure(disclosure: str) -> Tuple[str, Any]:
    try:
        arr = json.loads(b64u_decode(disclosure))
    except Exception as e:  # noqa: BLE001 — any parse failure is structural
        raise ProfileParseError(f"malformed disclosure: {e}") from e
    if (
        not isinstance(arr, list)
        or len(arr) != 3
        or not isinstance(arr[0], str)
        or not isinstance(arr[1], str)
    ):
        raise ProfileParseError("disclosure must be [salt, claim_name, claim_value]")
    return arr[1], arr[2]


def _walk(
    obj: Any,
    by_digest: Dict[str, str],
    seen_digests: Set[str],
    consumed: Set[str],
    top: bool = False,
) -> Any:
    """Resolve `_sd` digest arrays against the presented disclosures,
    recursively (structured claims, §16.2 — covers `asr.evidence`). Returns a
    resolved copy with `_sd`/`_sd_alg` stripped; the data model never sees
    encoding artifacts. A digest with no presented disclosure is simply
    withheld — R1b fails closed later if the data model requires that claim."""
    if isinstance(obj, list):
        return [_walk(v, by_digest, seen_digests, consumed) for v in obj]
    if not isinstance(obj, dict):
        return obj
    if "..." in obj:
        raise ProfileParseError("array-element disclosures ('...') are not part of sd-1")
    if "_sd_alg" in obj:
        if not top:
            raise ProfileParseError("_sd_alg is top-level only (RFC 9901)")
        if obj["_sd_alg"] != SD_ALG:
            raise ProfileParseError(f"_sd_alg is pinned to {SD_ALG!r} (§16.1, no negotiation)")
    out: Dict[str, Any] = {}
    for k, v in obj.items():
        if k in ("_sd", "_sd_alg"):
            continue
        out[k] = _walk(v, by_digest, seen_digests, consumed)
    sd = obj.get("_sd")
    if sd is not None:
        if not isinstance(sd, list) or not all(isinstance(x, str) for x in sd):
            raise ProfileParseError("_sd must be an array of digest strings")
        for dig in sd:
            if dig in seen_digests:
                raise ProfileParseError("duplicate digest in _sd")
            seen_digests.add(dig)
            disclosure = by_digest.get(dig)
            if disclosure is None:
                continue  # withheld by the holder — fail-closed at R1b if required
            name, value = _parse_disclosure(disclosure)
            if name in out:
                raise ProfileParseError(f"disclosure collides with existing claim {name!r}")
            consumed.add(dig)
            out[name] = _walk(value, by_digest, seen_digests, consumed)
    return out


class _Sd1Profile:
    """SD-JWT (RFC 9901) codec to the Profile contract (DESIGN §3, SPEC §16)."""

    id = "sd-1"
    receipt_typ = RECEIPT_TYP
    invocation_typ = INVOCATION_TYP
    result_typ = RESULT_TYP
    version = VERSION
    # Structural envelope family (the '~'-structure half of the REGISTRY
    # selection predicate; enforced by profiles.envelope_of + select_profile).
    envelope = "sd-jwt"

    def decode(self, artifact: str) -> Decoded:
        """R1a envelope: combined-form parse, base JWT parse + `alg==EdDSA`,
        pinned `_sd_alg`, digest-checked disclosure resolution (§16.2). Never
        checks typ/v (those are the selection predicate). `artifact_bytes` is
        the issuer-signed base (§16.4)."""
        if "~" not in artifact:
            raise ProfileParseError("sd-1 artifact must be an SD-JWT combined form")
        if not artifact.endswith("~"):
            raise ProfileParseError("combined form must end with '~' (no KB-JWT, §16.1)")
        segments = artifact[:-1].split("~")
        base, presented = segments[0], segments[1:]
        try:
            header, payload, signing_input, sig = _jws_decode(base)
        except Exception as e:  # noqa: BLE001 — any parse failure is structural
            raise ProfileParseError(str(e)) from e
        if header.get("alg") != "EdDSA":
            raise ProfileParseError("alg must be EdDSA (single-algorithm policy)")

        by_digest: Dict[str, str] = {}
        for d in presented:
            dig = _disclosure_digest(d)
            if dig in by_digest:
                raise ProfileParseError("duplicate disclosure presented")
            by_digest[dig] = d
        seen_digests: Set[str] = set()
        consumed: Set[str] = set()
        claims = _walk(payload, by_digest, seen_digests, consumed, top=True)
        if set(by_digest) - consumed:
            raise ProfileParseError(
                "presented disclosure matches no _sd digest (unknown or tampered disclosure)"
            )
        if (presented or seen_digests) and payload.get("_sd_alg") != SD_ALG:
            raise ProfileParseError("_sd_alg missing or not sha-256 (§16.1)")
        return Decoded(header, claims, signing_input, sig, base)

    def matches(self, header: Dict[str, Any], claims: Dict[str, Any]) -> bool:
        """Marker half of the selection predicate (REGISTRY sd-1 row): own typ,
        plus `v` for receipts/results (invocations carry no version claim).
        The `~`-combined-structure half is the envelope family, enforced by
        `profiles.select_profile` via `envelope_of` — a plain JWS re-tagged
        with an sd-jwt typ can never select sd-1."""
        typ = header.get("typ")
        if typ == self.receipt_typ or typ == self.result_typ:
            return claims.get("v") == self.version
        if typ == self.invocation_typ:
            return True
        return False

    def verify_sig(self, decoded: Decoded, resolver: KeyResolver, agent_id: str) -> bool:
        """R2 envelope signature over the ISSUER-SIGNED BASE's signing input.
        Disclosures are integrity-bound via the signed `_sd` digests, not by
        the signature directly."""
        return resolver.verify(agent_id, decoded.signing_input, decoded.sig)

    def serialize(self, signer: Signer, typ: str, claims: Dict[str, Any]) -> str:
        """Mint-side: split disclosable claims (module docstring) into salted
        disclosures, sign the base, emit the combined form. All disclosures
        are emitted; presenting a subset is the HOLDER's later choice.
        Invocations/results define no disclosable claims in this version
        (§16.1) — their combined form is `<JWT>~`."""
        payload = dict(claims)
        disclosures: List[str] = []
        if typ == self.receipt_typ:
            digests: List[str] = []
            for name in ("rid", "ext"):
                if name in payload:
                    d = _new_disclosure(name, payload.pop(name))
                    disclosures.append(d)
                    digests.append(_disclosure_digest(d))
            asr = payload.get("asr")
            if isinstance(asr, dict) and "evidence" in asr:
                asr = dict(asr)
                d = _new_disclosure("evidence", asr.pop("evidence"))
                disclosures.append(d)
                asr["_sd"] = [_disclosure_digest(d)]
                payload["asr"] = asr
            if digests:
                payload["_sd"] = digests
            if disclosures:
                payload["_sd_alg"] = SD_ALG
        base = _jws_sign(signer, typ, payload)
        return "~".join([base, *disclosures]) + "~"

    def canonicalize(self, obj: Dict[str, Any]) -> bytes:
        """RFC-8785 JCS, for hashing/signing preimages."""
        return canonical_json(obj)


SD1_PROFILE = _Sd1Profile()
