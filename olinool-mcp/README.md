# olinool-mcp

**The adoption wedge: a few lines give any single agent signed, scoped, replay-proof tool calls.**

Transport-agnostic middleware, deliberately NOT a live MCP server: `wrap_call` mints on egress (agent side), `guard` verifies on ingress (tool side). The envelope is a plain dict — put it in MCP metadata, an HTTP header, or a queue message. Every guarantee is olinool's (ayadi R1–R12: possession, audience, freshness, replay, scope); this package only binds the tool-call shape to it.

## The single-agent pattern

```python
from olinool import Signer, KeyResolver, Policy, mint_root
from olinool_mcp import wrap_call, guard

principal = Signer.generate("did:web:acme.example")          # the human/org authority
agent     = Signer.generate("did:web:acme.example:assistant")
resolver  = KeyResolver(); [resolver.register_signer(s) for s in (principal, agent)]

# 1. One root receipt, no onward delegation (max_depth=0).
r0 = mint_root(principal, agent.agent_id,
               scope=[{"act": "call", "res": "tool/*"}], ttl_s=3600, max_depth=0)

# 2. Agent side — wrap each tool call (mint-on-egress).
env = wrap_call([r0], agent, "did:web:tools.example", "search", {"q": "acme filings"})

# 3. Tool side — one gate before executing anything (verify-on-ingress).
decision = guard(env, resolver, Policy(), "did:web:tools.example")
assert decision.allowed
```

A stolen envelope replays as denied (`ERR_REPLAY`), an edited request breaks the possession hash (`ERR_POP`), a call outside the granted scope is refused (`ERR_TOOL_NOT_GRANTED`), and none of it needs a network call to verify.

## Normative conventions (pinned, v0.2)

1. **Request binding**: `request_bytes = canonical_json({"tool": tool_name, "arguments": arguments})` using moolam's RFC 8785 JCS. Both sides derive the bytes independently; the invocation's `req` hash binds them.
2. **Tool→grant mapping**: a tool call is `act: "call"`, `res: "tool/<tool_name>"`. `guard` = `verify_invocation` + `grant_permits(effective_scope, "call", "tool/<tool_name>")`. The single-agent root scope is `[{"act": "call", "res": "tool/*"}]`, narrowed as needed (optionally with `limits`).
3. **`ERR_TOOL_NOT_GRANTED` is package-local**: chain and invocation verified, but the effective scope does not cover this tool. It is not part of olinool's closed error set.

## Scope (v0.2, deliberate)

Core middleware only: no `mcp` SDK dependency, no live server, no network I/O. Core dependencies: `olinool` + `moolam` only.

Run: `pip install cryptography rfc8785 pytest && python -m pytest python/tests -q`

## Optional: MCP Extensions binding (`mcp_ext`, private prototype)

`olinool_mcp.mcp_ext` maps the envelope onto the MCP 2026-07-28 Extensions framework — `_meta` carriage under `io.github.codebysrini/olinool`, denials as one JSON-RPC code (`-31000`) with the closed `ERR_*` in `data.error`. It is CARRIAGE only (`attach_envelope`/`guard_request` call `wrap_call`/`guard` unchanged). The `mcp` SDK is an **optional extra** (`pip install .[mcp]`), imported defensively — core imports and the guard path run without it. Design + spec-verification: `EXTENSION_DRAFT.md`. **Prototype**: source-only in this repository, not released to PyPI. Demo: `python examples/mcp_server_demo.py`.
