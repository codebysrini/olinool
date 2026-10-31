"""olinool.errors — closed set of verification error codes (spec §7)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class MintError(Exception):
    """Raised when mint-time guards reject an attenuation request."""


# Closed enumeration — conformance vectors assert on these exact strings.
ERR_STRUCTURE = "ERR_STRUCTURE"
ERR_SIG = "ERR_SIG"
ERR_ROOT_UNTRUSTED = "ERR_ROOT_UNTRUSTED"
ERR_LINKAGE = "ERR_LINKAGE"
ERR_PARENT_HASH = "ERR_PARENT_HASH"
ERR_SCOPE_WIDENED = "ERR_SCOPE_WIDENED"
ERR_TIME_NOT_NESTED = "ERR_TIME_NOT_NESTED"
ERR_EXPIRED = "ERR_EXPIRED"
ERR_DEPTH = "ERR_DEPTH"
ERR_REVOKED_EPOCH = "ERR_REVOKED_EPOCH"
ERR_ASSURANCE = "ERR_ASSURANCE"
ERR_AUDIENCE = "ERR_AUDIENCE"
ERR_POP = "ERR_POP"
ERR_REPLAY = "ERR_REPLAY"
# Result records (spec §14, v0.2) — same closed-set discipline.
ERR_RESULT_STRUCTURE = "ERR_RESULT_STRUCTURE"
ERR_RESULT_SIG = "ERR_RESULT_SIG"
ERR_RESULT_BINDING = "ERR_RESULT_BINDING"
# Profiles (v0.3) — encoding selection, before any claim logic (design §5).
ERR_PROFILE_NOT_ALLOWED = "ERR_PROFILE_NOT_ALLOWED"
ERR_PROFILE_MIXED = "ERR_PROFILE_MIXED"


@dataclass
class Decision:
    allowed: bool
    error: Optional[str] = None
    detail: Optional[str] = None
    effective_scope: Optional[list] = None  # leaf scope if allowed

    @classmethod
    def deny(cls, error: str, detail: str = "") -> "Decision":
        return cls(allowed=False, error=error, detail=detail)

    @classmethod
    def allow(cls, effective_scope: list) -> "Decision":
        return cls(allowed=True, effective_scope=effective_scope)
