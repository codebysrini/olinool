"""dabba.model — the Dabba (Lid + append-only Tiers + seal chain).

Crypto is entirely moolam's; this module is data structures + the seal press
applied to tiers. No policy, no scopes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from moolam import Signer, jws_sign, sha256_b64u
from moolam.core import canonical_json

SEAL_TYP = "dabba-seal+jws"
SEAL_VH_TYP = "dabba-seal-vh+jws"

PROFILE_SEAL_1 = "seal-1"        # the v0.1 seal format, retroactively named; FROZEN
PROFILE_SEAL_VH_1 = "seal-vh-1"  # SPEC §9.1: authenticated instructions + attested views
SEAL_TYP_BY_PROFILE = {PROFILE_SEAL_1: SEAL_TYP, PROFILE_SEAL_VH_1: SEAL_VH_TYP}


@dataclass
class Lid:
    goal: str
    route: List[str]                      # ordered agent ids, one per planned hop
    ttl: int                              # unix seconds
    gov: Optional[Dict[str, Any]] = None  # olinool receipt-chain ref (bridge only)
    deps: Dict[int, List[int]] = field(default_factory=dict)  # hop -> prior tier idxs it may read
    profile: str = PROFILE_SEAL_1
    instructions: Optional[List[str]] = None  # seal-vh-1 only: one per routed hop, sealed in the core

    def core_obj(self) -> Dict[str, Any]:
        """The immutable, authenticated core of the Lid.

        Every tier seal commits to sha256(core_bytes()), so tampering with any
        of these fields after even one hop has sealed breaks the chain. `deps`
        is included precisely because it governs what each hop may read (the V1
        guarantee) — leaving it unauthenticated would let a Dabba holder widen a
        hop's read access undetected. `gov` is EXCLUDED: the bridge may pin an
        olinool receipt chain after sealing, and those receipts are self-
        authenticating anyway (swapping the pointer cannot forge authority). v0
        treats the core as fixed at Dabba creation; dynamic re-routing is later.

        Under seal-vh-1 the core additionally carries `profile` and
        `instructions` (SPEC §9.1a): sealing the instruction channel at creation
        is what closes audit Limitation A, and sealing the profile id is what
        makes profile-stripping detectable. seal-1 cores stay byte-identical to
        v0.1.
        """
        o: Dict[str, Any] = {"goal": self.goal, "route": list(self.route), "ttl": self.ttl,
                             "deps": {str(k): v for k, v in sorted(self.deps.items())}}
        if self.profile == PROFILE_SEAL_VH_1:
            o["profile"] = self.profile
            o["instructions"] = list(self.instructions or [])
        return o

    def core_bytes(self) -> bytes:
        return canonical_json(self.core_obj())

    def to_obj(self) -> Dict[str, Any]:
        o = self.core_obj()
        if self.gov is not None:
            o["gov"] = self.gov
        return o


@dataclass
class Tier:
    hop: int
    writer: str        # agent id that produced this tier (must equal route[hop])
    body: str          # the agent's output text

    def to_obj(self) -> Dict[str, Any]:
        return {"hop": self.hop, "writer": self.writer, "body": self.body}

    def bytes(self) -> bytes:
        return canonical_json(self.to_obj())


@dataclass
class Dabba:
    lid: Lid
    tiers: List[Tier] = field(default_factory=list)
    seals: List[str] = field(default_factory=list)  # compact JWS seals, hash-linked

    def seal_tier(self, tier: Tier, signer: Signer, view_hash: Optional[str] = None) -> None:
        """Append a tier and its seal. Seal binds tier bytes + previous seal hash.

        Under seal-vh-1 the seal additionally binds `view_hash` — the hash of
        the W(hop) the agent was shown (SPEC §9.1b) — and is mandatory; under
        seal-1 supplying one is an error (frozen format carries no such field).
        """
        if signer.agent_id != tier.writer:
            raise ValueError(f"signer {signer.agent_id!r} is not tier writer {tier.writer!r}")
        prev = sha256_b64u(self.seals[-1].encode("ascii")) if self.seals else None
        payload = {"tier_hash": sha256_b64u(tier.bytes()), "prev": prev,
                   "hop": tier.hop, "writer": tier.writer,
                   "lid_hash": sha256_b64u(self.lid.core_bytes())}
        if self.lid.profile == PROFILE_SEAL_VH_1:
            if view_hash is None:
                raise ValueError("seal-vh-1 seals must bind a view_hash")
            payload["view_hash"] = view_hash
        elif view_hash is not None:
            raise ValueError(f"profile {self.lid.profile!r} seals carry no view_hash")
        typ = SEAL_TYP_BY_PROFILE.get(self.lid.profile)
        if typ is None:
            raise ValueError(f"unknown seal profile {self.lid.profile!r}")
        self.tiers.append(tier)
        self.seals.append(jws_sign(signer, typ, payload))
