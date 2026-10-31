"""olinool-mcp — the adoption wedge: signed, scoped, replay-proof tool calls
for a single agent, in a few lines.

Transport-agnostic middleware, NOT a live MCP server: `wrap_call` runs on the
agent side (mint-on-egress), `guard` runs on the tool side (verify-on-ingress).
The envelope is a plain dict — carry it in MCP metadata, an HTTP header, or a
queue message; the crypto neither knows nor cares.

Normative request-binding rule (also recorded in this package's README):

    request_bytes = canonical_json({"tool": tool_name, "arguments": arguments})

using moolam's RFC 8785 JCS, so both sides derive identical bytes without
shipping them.

Tool→grant convention: a tool call maps to act "call", res "tool/<tool_name>".
`guard` is a thin binding over ayadi: verify_invocation (R1–R12) plus
grant_permits(effective_scope, "call", "tool/<tool_name>").

ERR_TOOL_NOT_GRANTED is package-local — chain and invocation verified, but the
effective scope does not cover this tool. It is NOT part of olinool's closed
error set (those cover artifact verification; this is the receiver's scope
gate on one concrete call).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from moolam.core import canonical_json
from olinool import Decision, KeyResolver, Policy, Signer, invoke, verify_invocation
from olinool.scopes import grant_permits

__version__ = "0.1.0"

ERR_TOOL_NOT_GRANTED = "ERR_TOOL_NOT_GRANTED"


def request_bytes(tool_name: str, arguments: Dict[str, Any]) -> bytes:
    """The normative binding: JCS over {"tool": ..., "arguments": ...}."""
    return canonical_json({"tool": tool_name, "arguments": arguments})


def wrap_call(
    chain: List[str],
    actor: Signer,
    receiver_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Mint-on-egress: bind one tool call to the chain's leaf receipt (PoP)."""
    invocation = invoke(chain[-1], actor, receiver_id, request_bytes(tool_name, arguments))
    return {"tool": tool_name, "arguments": arguments, "chain": list(chain), "invocation": invocation}


def guard(
    envelope: Dict[str, Any],
    resolver: KeyResolver,
    policy: Optional[Policy],
    receiver_id: str,
) -> Decision:
    """Verify-on-ingress: the tool-side gate.

    Re-derives the request bytes from the envelope's own tool/arguments, so a
    tampered request breaks the possession hash (ERR_POP) and a tool outside
    the granted scope is denied (ERR_TOOL_NOT_GRANTED).
    """
    policy = policy or Policy()
    tool_name = envelope["tool"]
    d = verify_invocation(
        envelope["chain"],
        envelope["invocation"],
        request_bytes(tool_name, envelope["arguments"]),
        receiver_id,
        resolver,
        policy,
    )
    if not d.allowed:
        return d
    if not grant_permits(d.effective_scope, "call", f"tool/{tool_name}"):
        return Decision.deny(ERR_TOOL_NOT_GRANTED, f"scope does not cover tool {tool_name!r}")
    return d
