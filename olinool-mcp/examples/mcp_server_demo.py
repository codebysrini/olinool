#!/usr/bin/env python3
"""Runnable demo: one guarded MCP tool, over the olinool extension carriage.

A minimal in-process MCP-shaped server exposes ONE guarded tool (`search`) and
verifies every `tools/call` at ingress with the REAL guard path
(`olinool_mcp.mcp_ext.guard_request`). A client calls it three ways:

  1. valid chain, in-scope tool           -> allowed, tool runs
  2. valid chain, out-of-scope tool        -> denied, JSON-RPC -31000
  3. forged (tampered) chain               -> denied, JSON-RPC -31000

No network and no SDK are required: the transport is an in-process function call
(the envelope is plain JSON either way), but the verification is the production
gate, unchanged. If the `mcp` extra is installed, mcp_ext.HAVE_MCP is True and
the same params dicts are exactly what mcp.types.CallToolRequestParams serialize
to — the carriage does not depend on it.

Run:  python olinool-mcp/examples/mcp_server_demo.py
"""
from __future__ import annotations

import json

from olinool import KeyResolver, Policy, Signer, mint_root
from olinool_mcp.mcp_ext import (
    HAVE_MCP,
    attach_envelope,
    denial_to_jsonrpc_error,
    guard_request,
)

SERVER_ID = "did:web:tools.example"          # stdio server: its registered agent id (§2)


class GuardedToolServer:
    """The tool side. One olinool gate before any tool executes (draft §3)."""

    def __init__(self, resolver: KeyResolver):
        self.resolver = resolver
        self.policy = Policy()               # holds the one piece of state: the nonce cache
        self.tools = {"search": lambda args: {"hits": [f"result for {args.get('q')!r}"]}}

    def handle_tools_call(self, request: dict) -> dict:
        """Verify at the door; execute only if the Decision allows."""
        params = request["params"]
        decision = guard_request(params, self.resolver, self.policy, SERVER_ID)
        if not decision.allowed:
            return denial_to_jsonrpc_error(decision, request["id"])
        output = self.tools[params["name"]](params.get("arguments", {}))
        return {"jsonrpc": "2.0", "id": request["id"],
                "result": {"resultType": "complete",
                           "content": [{"type": "text", "text": json.dumps(output)}]}}


def call(server, req_id, chain, actor, tool, args):
    """The agent side: build tools/call params and attach the envelope (§2)."""
    params = {"name": tool, "arguments": args}
    attach_envelope(params, chain, actor, SERVER_ID)
    request = {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": params}
    request = json.loads(json.dumps(request))          # real wire round-trip
    return server.handle_tools_call(request)


def _show(label, resp):
    if "error" in resp:
        e = resp["error"]
        print(f"  {label}: DENIED  code={e['code']}  {e['data']['error']} — {e['data']['detail']}")
    else:
        print(f"  {label}: ALLOWED {resp['result']['content'][0]['text']}")


def main() -> None:
    principal = Signer.generate("did:web:acme.example")
    agent = Signer.generate("did:web:acme.example:assistant")
    resolver = KeyResolver()
    for s in (principal, agent):
        resolver.register_signer(s)

    # Authority: this agent may call search tools only, no onward delegation.
    root = mint_root(principal, agent.agent_id,
                     scope=[{"act": "call", "res": "tool/search*"}],
                     ttl_s=600, max_depth=0)
    chain = [root]
    server = GuardedToolServer(resolver)

    print(f"olinool MCP-extension demo  (mcp SDK present: {HAVE_MCP})\n")

    _show("1. valid + in-scope ", call(server, 1, chain, agent, "search", {"q": "acme filings"}))
    _show("2. valid + over-scope", call(server, 2, chain, agent, "drop_tables", {"db": "prod"}))

    # 3. Forge the chain: tamper the leaf receipt's signature after minting.
    params = {"name": "search", "arguments": {"q": "acme"}}
    attach_envelope(params, chain, agent, SERVER_ID)
    from olinool_mcp.mcp_ext import EXTENSION_ID
    leaf = params["_meta"][EXTENSION_ID]["chain"][-1]
    params["_meta"][EXTENSION_ID]["chain"][-1] = leaf[:-2] + ("A" if leaf[-1] != "A" else "B")
    forged_req = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": params}
    _show("3. forged chain     ", server.handle_tools_call(json.loads(json.dumps(forged_req))))


if __name__ == "__main__":
    main()
