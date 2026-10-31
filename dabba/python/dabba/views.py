"""dabba.views — scoped working view W(k) construction enforcing invariant V1.

This is the security-relevant module: it is the *only* place a downstream hop's
context is assembled, and it is constructed to make leakage structurally
impossible rather than filtered after the fact. A hop sees its goal, its
instruction, and ONLY the prior-tier bodies the route explicitly declared as
its inputs (Lid.deps[hop]). Everything else in the Dabba is never placed in
the view, so it cannot leak.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from moolam.core import canonical_json

from .model import PROFILE_SEAL_VH_1, Dabba


@dataclass
class WorkingView:
    goal: str
    instruction: str
    inputs: List[str]  # bodies of declared prior tiers only

    def as_prompt(self) -> str:
        parts = [f"Lid: {self.goal}", f"Instruction: {self.instruction}"]
        if self.inputs:
            parts.append("Input facts:\n" + "\n".join(self.inputs))
        return "\n".join(parts)

    def canonical_bytes(self) -> bytes:
        """The view_hash preimage (SPEC §9.1b): canonical JSON of the view's
        fields, NOT as_prompt() — prompt layout is presentation, not identity."""
        return canonical_json({"goal": self.goal, "instruction": self.instruction,
                               "inputs": list(self.inputs)})


def build_view(dabba: Dabba, hop: int, instruction: Optional[str] = None) -> WorkingView:
    """Construct W(hop). Only tiers listed in Lid.deps[hop] are included.

    V1 is enforced by construction: we read exactly the declared indices and
    copy nothing else. A hop with no declared deps gets an empty inputs list.

    Instruction sourcing is profile-dependent (SPEC §9.1a): under seal-1 the
    caller supplies it (and MUST keep it routing metadata only — Limitation A);
    under seal-vh-1 it comes from the sealed Lid core and a caller-supplied one
    is rejected, so the instruction channel structurally cannot carry tier
    content.
    """
    if dabba.lid.profile == PROFILE_SEAL_VH_1:
        if instruction is not None:
            raise ValueError("seal-vh-1: instruction comes from the sealed Lid, not the caller")
        instrs = dabba.lid.instructions or []
        if hop < 0 or hop >= len(instrs):
            raise IndexError(f"hop {hop} has no sealed instruction (instructions len {len(instrs)})")
        instruction = instrs[hop]
    elif instruction is None:
        raise ValueError(f"profile {dabba.lid.profile!r}: caller must supply the instruction")
    declared = dabba.lid.deps.get(hop, [])
    inputs: List[str] = []
    for idx in declared:
        if idx < 0 or idx >= len(dabba.tiers):
            raise IndexError(f"hop {hop} declares dep on nonexistent tier {idx}")
        if idx >= hop:
            raise ValueError(f"hop {hop} may only read earlier tiers, not {idx}")
        inputs.append(dabba.tiers[idx].body)
    return WorkingView(goal=dabba.lid.goal, instruction=instruction, inputs=inputs)
