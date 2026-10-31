"""moolam.jws — minimal compact-JWS seal press (EdDSA only, no negotiation).

This is the seal both olinool (delegation receipts) and dabba (task tiers)
press onto their artifacts. Single algorithm by policy: downgrade attacks are
rejected structurally by every verifier in the stack (olinool test c20).
Production note: swap for a battle-tested JOSE library at 1.0; the format is
standard compact JWS either way.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .core import b64u_decode, b64u_encode, canonical_json
from .keys import Signer


def jws_sign(signer: Signer, typ: str, payload: Dict[str, Any]) -> str:
    header = {"alg": "EdDSA", "typ": typ, "kid": signer.agent_id}
    h = b64u_encode(canonical_json(header))
    p = b64u_encode(canonical_json(payload))
    signing_input = f"{h}.{p}".encode("ascii")
    sig = b64u_encode(signer.sign(signing_input))
    return f"{h}.{p}.{sig}"


def jws_decode(jws: str) -> Tuple[Dict[str, Any], Dict[str, Any], bytes, bytes]:
    """Return (header, payload, signing_input, signature). Raises ValueError."""
    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("JWS must have three segments")
    h_b, p_b, s_b = parts
    header = json.loads(b64u_decode(h_b))
    payload = json.loads(b64u_decode(p_b))
    return header, payload, f"{h_b}.{p_b}".encode("ascii"), b64u_decode(s_b)
