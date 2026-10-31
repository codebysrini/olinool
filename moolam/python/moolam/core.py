"""moolam.core — canonical encoding and hashing shared by the whole stack.

Canonical JSON is RFC 8785 (JCS) via the rfc8785 package, as the specs pin.
For the all-ASCII claim sets the stack minted before v0.2 the output is
byte-identical to the previous json.dumps(sort_keys=True, separators=(",", ":"),
ensure_ascii=True) prototype encoder — test_canonical_json_v01_byte_parity
guards that wire compatibility.
"""
from __future__ import annotations

import base64
import hashlib
from typing import Any

import rfc8785


def b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def canonical_json(obj: Any) -> bytes:
    return rfc8785.dumps(obj)


def sha256_b64u(data: bytes) -> str:
    return b64u_encode(hashlib.sha256(data).digest())
