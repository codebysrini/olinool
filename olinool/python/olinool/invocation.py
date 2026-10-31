"""olinool.invocation — proof-of-possession binding (spec §6).

A Receipt chain alone is BEARER material: anyone who observes it could
replay it. The Invocation closes that hole: the leaf *subject* signs a
short-lived statement binding (leaf receipt, concrete request, receiver,
nonce). A receiver accepts an action only with a valid Invocation.

Payload:
  typ   "olinool-invocation"
  rcp   b64u sha256 of the leaf receipt JWS
  sub   leaf subject id (redundant, aids logging)
  aud   the receiver's id — exact match required
  req   b64u sha256 of the concrete request bytes
  iat   seconds
  nnc   random nonce (replay cache key)
"""
from __future__ import annotations

import secrets
import time
from typing import Any, Dict, Optional

from .core import sha256_b64u
from .keys import Signer
from .muthirai import receipt_hash
from .profiles.jws1 import JWS1_PROFILE

INVOCATION_TYP = "olinool-invocation+jws"


def invoke(
    leaf_receipt_jws: str,
    subject: Signer,
    receiver_id: str,
    request_bytes: bytes,
    now: Optional[int] = None,
    nonce: Optional[str] = None,
) -> str:
    payload: Dict[str, Any] = {
        "typ": "olinool-invocation",
        "rcp": receipt_hash(leaf_receipt_jws),
        "sub": subject.agent_id,
        "aud": receiver_id,
        "req": sha256_b64u(request_bytes),
        "iat": int(now if now is not None else time.time()),
        "nnc": nonce if nonce is not None else secrets.token_urlsafe(16),
    }
    return JWS1_PROFILE.serialize(subject, INVOCATION_TYP, payload)
