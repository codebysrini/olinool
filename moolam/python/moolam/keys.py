"""moolam.keys — Ed25519 signing/verification + key resolution seam.

KeyResolver is the seam where A2A Agent Cards / .well-known documents plug
in. The prototype uses an in-memory map; production resolves
`https://<domain>/.well-known/...` and caches with a bounded TTL.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .core import b64u_decode, b64u_encode


@dataclass
class Signer:
    """An agent's signing identity."""

    agent_id: str
    private_key: Ed25519PrivateKey

    @classmethod
    def generate(cls, agent_id: str) -> "Signer":
        return cls(agent_id=agent_id, private_key=Ed25519PrivateKey.generate())

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()

    @property
    def public_key_b64u(self) -> str:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            PublicFormat,
        )

        return b64u_encode(self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw))

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(data)


class KeyResolver:
    """Maps agent id -> Ed25519 public key. Stand-in for Agent Card lookup."""

    def __init__(self) -> None:
        self._keys: Dict[str, Ed25519PublicKey] = {}

    def register(self, agent_id: str, public_key_b64u: str) -> None:
        raw = b64u_decode(public_key_b64u)
        self._keys[agent_id] = Ed25519PublicKey.from_public_bytes(raw)

    def register_signer(self, signer: Signer) -> None:
        self.register(signer.agent_id, signer.public_key_b64u)

    def resolve(self, agent_id: str) -> Optional[Ed25519PublicKey]:
        return self._keys.get(agent_id)

    def verify(self, agent_id: str, data: bytes, sig: bytes) -> bool:
        key = self.resolve(agent_id)
        if key is None:
            return False
        try:
            key.verify(sig, data)
            return True
        except InvalidSignature:
            return False
