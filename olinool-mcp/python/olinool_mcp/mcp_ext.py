"""olinool_mcp.mcp_ext — MCP Extension carriage for the olinool wedge.

OPTIONAL submodule (EXTENSION_DRAFT.md). Maps the transport-agnostic
olinool-mcp envelope onto the MCP 2026-07-28 Extensions framework: the two
olinool artifacts ({chain, invocation}) ride in a `tools/call` request's
`_meta` under one extension key; a denial maps to a single JSON-RPC transport
error code with the closed ERR_* vocabulary carried in `data.error`.

This module is CARRIAGE, not semantics (EXTENSION_DRAFT §6): every guarantee
is olinool's. `attach_envelope` calls `olinool_mcp.wrap_call` and
`guard_request` calls `olinool_mcp.guard` — both unchanged. There is no
verification logic here; if you find yourself re-deriving a rule, call the
library instead.

The official `mcp` Python SDK is an OPTIONAL extra: it is imported defensively
(guard.py-style fail-open) so `olinool-mcp` core still imports without it. The
guard path is plain-dict and never needs the SDK — the SDK, when present, only
provides typed params/result models for callers who want them.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from olinool import Decision, KeyResolver, Policy, Signer
from olinool.errors import ERR_STRUCTURE

from . import guard, wrap_call

# Optional MCP SDK. Absent in the core test matrix; present under the `mcp`
# extra. Never required by the guard path — fail open on import, like guard.py.
try:  # pragma: no cover - covered by the `mcp` extra, absent in core matrix
    import mcp.types as _mcp_types  # noqa: F401

    HAVE_MCP = True
except ImportError:  # pragma: no cover
    _mcp_types = None
    HAVE_MCP = False

# Extension identity (EXTENSION_DRAFT §1, decided §0.1). Reverse-DNS vendor
# prefix owned via the GitHub namespace; name is the locked concept name.
# Second label is `github`, so the prefix is NOT MCP-reserved (spec §_meta).
EXTENSION_ID = "io.github.codebysrini/olinool"

# One transport code for ALL olinool denials (EXTENSION_DRAFT §3, decided §0.4).
# Verified §7: outside the JSON-RPC reserved range -32768..-32000 AND clear of
# the spec-reserved implementation band -32020..-32099.
OLINOOL_DENIED_CODE = -31000

OLINOOL_DENIED_MESSAGE = "olinool: authorization denied"


def attach_envelope(
    params: Dict[str, Any],
    chain: List[str],
    actor: Signer,
    receiver_id: str,
) -> Dict[str, Any]:
    """Client side: mint the invocation for this call and insert the envelope.

    `params` is an MCP `tools/call` params object ({name, arguments, ...}).
    Mints via `wrap_call` (mint-on-egress) and writes {chain, invocation} into
    ``params["_meta"][EXTENSION_ID]``. Returns the SAME params dict, mutated.

    No new top-level fields (EXTENSION_DRAFT §2): `tool` and `arguments` are
    already `params.name`/`params.arguments`, so only the two artifacts are
    added. request_bytes cover name+arguments ONLY, never `_meta` — so the
    mandatory io.modelcontextprotocol/* protocol fields and the envelope itself
    stay outside the signed bytes.
    """
    tool_name = params["name"]
    arguments = params.get("arguments", {})
    env = wrap_call(chain, actor, receiver_id, tool_name, arguments)
    meta = params.setdefault("_meta", {})
    meta[EXTENSION_ID] = {"chain": env["chain"], "invocation": env["invocation"]}
    return params


def guard_request(
    params: Dict[str, Any],
    resolver: KeyResolver,
    policy: Optional[Policy],
    receiver_id: str,
) -> Decision:
    """Server side: the `tools/call` ingress gate (EXTENSION_DRAFT §3).

    Extracts the envelope from ``params["_meta"][EXTENSION_ID]`` and derives
    request_bytes from the request's OWN name/arguments (no request bytes are
    ever shipped), then runs the five-step check via `olinool_mcp.guard`
    unchanged.

    Absence of artifacts is not a scope decision: a guarded call missing the
    envelope (or missing a tool name) fails closed with ERR_STRUCTURE — never a
    scope code (EXTENSION_DRAFT §3).
    """
    if "name" not in params:
        return Decision.deny(ERR_STRUCTURE, "olinool: malformed tools/call params (no name)")
    meta = params.get("_meta") or {}
    ext = meta.get(EXTENSION_ID)
    if not isinstance(ext, dict) or "chain" not in ext or "invocation" not in ext:
        return Decision.deny(ERR_STRUCTURE, "olinool: no envelope in request _meta")
    envelope = {
        "tool": params["name"],
        "arguments": params.get("arguments", {}),
        "chain": ext["chain"],
        "invocation": ext["invocation"],
    }
    return guard(envelope, resolver, policy, receiver_id)


def denial_to_jsonrpc_error(decision: Decision, req_id: Any) -> Dict[str, Any]:
    """Map an olinool denial to a JSON-RPC error response object (§3).

    ONE transport code (OLINOOL_DENIED_CODE) for every olinool denial; the
    closed ERR_* rides untouched in ``data.error``, its human detail in
    ``data.detail``. The olinool taxonomy stays closed; the transport code is
    theirs (instinct 11). Raises if handed an allowed Decision — a denial error
    object must never be minted for a call that passed.
    """
    if decision.allowed:
        raise ValueError("denial_to_jsonrpc_error called on an allowed Decision")
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": OLINOOL_DENIED_CODE,
            "message": OLINOOL_DENIED_MESSAGE,
            "data": {"error": decision.error, "detail": decision.detail or ""},
        },
    }
