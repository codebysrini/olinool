"""dabba.bridge — optional cross-link between authority and action.

Imported by dabba/__init__ ONLY when olinool is installed. It never changes
dabba's standalone behavior; it adds:

  put_receipt_in_lid(lid, chain)   — pin an olinool receipt chain in Lid.gov
  tier_as_result(dabba, hop, ...)  — emit a SIGNED `olinool-result` record
                                     (compact JWS, spec §14) for a sealed
                                     tier: the tier writer attests its own
                                     output bytes against the leaf receipt

The authority chain (olinool receipts) proves who was ALLOWED to act at each
hop; the action chain (dabba seals) proves what they DID. Cross-linked by
hash, they are the two halves of an auditable delegation — and the result
record is exactly the artifact olinool needs before claiming "self-auditing".
"""
from __future__ import annotations

from typing import List

from moolam import Signer, sha256_b64u
from olinool import mint_result

from .model import Dabba, Lid


def put_receipt_in_lid(lid: Lid, receipt_chain: List[str]) -> None:
    """Pin an olinool receipt chain (by per-hop hash) into the Lid."""
    lid.gov = {
        "scheme": "olinool/0.1",
        "chain_hashes": [sha256_b64u(r.encode("ascii")) for r in receipt_chain],
    }


def tier_as_result(dabba: Dabba, hop: int, receipt_jws: str, actor: Signer,
                   status: str = "completed") -> str:
    """Press a signed olinool-result (compact JWS) onto a sealed tier's output.

    The actor must be the tier's writer AND the receipt's leaf subject
    (mint_result enforces the latter). Output bytes = the tier body, so the
    record's `out` hash cross-links the action chain to the authority chain.
    """
    tier = dabba.tiers[hop]
    if actor.agent_id != tier.writer:
        raise ValueError(f"actor {actor.agent_id!r} is not tier writer {tier.writer!r}")
    return mint_result(receipt_jws, actor, tier.body.encode("utf-8"), status=status)
