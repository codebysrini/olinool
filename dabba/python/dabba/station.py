"""dabba.station — in-process custodian + seal-chain verifier (rules S1–S7).

The Station holds a Dabba, constructs each hop's scoped view (delegating to
views.build_view so V1 holds), appends sealed tiers, and verifies the chain
offline. No network, no persistence — the Sorting Station reduced to exactly
what dap-bench exercised.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set

from moolam import KeyResolver, Signer, jws_decode, sha256_b64u

from .model import (
    PROFILE_SEAL_1,
    PROFILE_SEAL_VH_1,
    SEAL_TYP_BY_PROFILE,
    Dabba,
    Lid,
    Tier,
)
from .views import WorkingView, build_view

ERR_STRUCTURE = "ERR_STRUCTURE"
ERR_SIG = "ERR_SIG"
ERR_SEAL_LINK = "ERR_SEAL_LINK"
ERR_TIER_HASH = "ERR_TIER_HASH"
ERR_ROUTE = "ERR_ROUTE"
ERR_EXPIRED = "ERR_EXPIRED"
ERR_LID = "ERR_LID"
ERR_VIEW_LEAK = "ERR_VIEW_LEAK"
ERR_PROFILE_NOT_ALLOWED = "ERR_PROFILE_NOT_ALLOWED"
ERR_PROFILE_MIXED = "ERR_PROFILE_MIXED"
ERR_VIEW_HASH = "ERR_VIEW_HASH"


@dataclass
class Verdict:
    ok: bool
    error: Optional[str] = None
    detail: str = ""


class Station:
    def __init__(self, dabba: Dabba, resolver: KeyResolver, clock_skew_s: int = 60,
                 allowed_profiles: Optional[Set[str]] = None):
        self.dabba = dabba
        self.resolver = resolver
        self.clock_skew_s = clock_skew_s
        # SPEC §9 rule S0: acceptance by verifier policy, default the incumbent
        # only — opting into seal-vh-1 is explicit, never negotiated.
        self.allowed_profiles = set(allowed_profiles) if allowed_profiles is not None \
            else {PROFILE_SEAL_1}

    def view_for(self, hop: int, instruction: Optional[str] = None) -> WorkingView:
        return build_view(self.dabba, hop, instruction)

    def run_hop(self, hop: int, instruction: Optional[str], signer: Signer,
                agent_fn: Callable[[WorkingView], str]) -> Tier:
        """Give the agent its scoped view, seal whatever it returns.

        seal-vh-1: `instruction` must be None (it comes from the sealed Lid),
        and the pressed seal binds the hash of the exact view delivered here.
        """
        if signer.agent_id != self.dabba.lid.route[hop]:
            raise ValueError(f"signer {signer.agent_id!r} not assigned to hop {hop}")
        view = self.view_for(hop, instruction)
        body = agent_fn(view)
        tier = Tier(hop=hop, writer=signer.agent_id, body=body)
        vh = sha256_b64u(view.canonical_bytes()) \
            if self.dabba.lid.profile == PROFILE_SEAL_VH_1 else None
        self.dabba.seal_tier(tier, signer, view_hash=vh)
        return tier

    def verify(self, now: Optional[int] = None) -> Verdict:
        d = self.dabba
        t_now = int(now if now is not None else time.time())
        # S0 — profile gate, before any seal is opened (SPEC §9).
        profile = d.lid.profile or PROFILE_SEAL_1
        expected_typ = SEAL_TYP_BY_PROFILE.get(profile)
        if profile not in self.allowed_profiles or expected_typ is None:
            return Verdict(False, ERR_PROFILE_NOT_ALLOWED,
                           f"profile {profile!r} not in verifier allow-list")
        vh_profile = profile == PROFILE_SEAL_VH_1
        if len(d.tiers) != len(d.seals):
            return Verdict(False, ERR_STRUCTURE, "tiers/seals length mismatch")
        if not d.lid.goal or not d.lid.route:
            return Verdict(False, ERR_STRUCTURE, "lid missing goal/route")
        if vh_profile and (not isinstance(d.lid.instructions, list)
                           or len(d.lid.instructions) != len(d.lid.route)):
            return Verdict(False, ERR_STRUCTURE,
                           "seal-vh-1: instructions must cover every routed hop")
        lid_hash = sha256_b64u(d.lid.core_bytes())
        for i, (tier, seal) in enumerate(zip(d.tiers, d.seals)):
            try:
                header, payload, signing_input, sig = jws_decode(seal)
            except Exception as e:  # noqa: BLE001
                return Verdict(False, ERR_STRUCTURE, f"seal {i}: {e}")
            if header.get("alg") != "EdDSA":
                return Verdict(False, ERR_STRUCTURE, f"seal {i}: bad header")
            if header.get("typ") != expected_typ:
                return Verdict(False, ERR_PROFILE_MIXED,
                               f"seal {i}: typ {header.get('typ')!r} is not profile "
                               f"{profile!r}'s {expected_typ!r}")
            if header.get("kid") != tier.writer or not self.resolver.verify(tier.writer, signing_input, sig):
                return Verdict(False, ERR_SIG, f"seal {i}: signature invalid for {tier.writer!r}")
            prev = sha256_b64u(d.seals[i - 1].encode("ascii")) if i > 0 else None
            if payload.get("prev") != prev:
                return Verdict(False, ERR_SEAL_LINK, f"seal {i}: prev-hash mismatch")
            if payload.get("tier_hash") != sha256_b64u(tier.bytes()):
                return Verdict(False, ERR_TIER_HASH, f"tier {i}: content does not match seal")
            if payload.get("lid_hash") != lid_hash:
                return Verdict(False, ERR_LID, f"seal {i}: Lid core (goal/route/ttl/deps) was altered after sealing")
            if payload.get("hop") != i or tier.hop != i:
                return Verdict(False, ERR_ROUTE, f"tier {i}: hop index does not match position")
            if i >= len(d.lid.route) or tier.writer != d.lid.route[i]:
                return Verdict(False, ERR_ROUTE, f"tier {i}: writer not the routed agent")
            if vh_profile:
                # S9 — the attested view must equal W(i) reconstructed from the
                # sealed Dabba alone (SPEC §9.1b). Sound at this point: the Lid
                # core is authenticated (S7 above) and every dep of hop i is an
                # earlier tier whose hash this loop already verified (S5).
                try:
                    expected_view = build_view(d, i)
                except Exception as e:  # noqa: BLE001
                    return Verdict(False, ERR_STRUCTURE, f"seal {i}: view reconstruction failed: {e}")
                if payload.get("view_hash") != sha256_b64u(expected_view.canonical_bytes()):
                    return Verdict(False, ERR_VIEW_HASH,
                                   f"seal {i}: attested view does not match the declared W({i})")
        if t_now > d.lid.ttl + self.clock_skew_s:
            return Verdict(False, ERR_EXPIRED, "dabba past ttl")
        return Verdict(True)


def audit_view_no_leak(view: WorkingView, forbidden: List[str]) -> Optional[str]:
    """Test helper for V1: return the first forbidden string that leaked into
    the serialized view, or None. Used by the leakage conformance vectors."""
    blob = view.as_prompt()
    for s in forbidden:
        if s in blob:
            return s
    return None
