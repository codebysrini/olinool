"""olinool_mcp.mcp_ext — MCP Extension carriage tests.

Proves the carriage layer (EXTENSION_DRAFT §2–§4) preserves every olinool
guarantee and maps denials to the single JSON-RPC transport code. The semantics
are already covered by test_olinool_mcp.py; here we assert the `_meta` binding,
the error mapping, statelessness, and the OAuth-vs-olinool layer separation.
"""
from __future__ import annotations

import json

import pytest

from olinool import KeyResolver, Policy, Signer, mint_root
from olinool.errors import ERR_STRUCTURE
from olinool_mcp import ERR_TOOL_NOT_GRANTED
from olinool_mcp.mcp_ext import (
    EXTENSION_ID,
    OLINOOL_DENIED_CODE,
    attach_envelope,
    denial_to_jsonrpc_error,
    guard_request,
)

TOOL_SERVER = "did:web:tools.example"


@pytest.fixture
def world():
    principal = Signer.generate("did:web:acme.example")
    agent = Signer.generate("did:web:acme.example:assistant")
    resolver = KeyResolver()
    for s in (principal, agent):
        resolver.register_signer(s)
    r0 = mint_root(principal, agent.agent_id,
                   scope=[{"act": "call", "res": "tool/search*"}],
                   ttl_s=600, max_depth=0)
    return dict(agent=agent, resolver=resolver, chain=[r0])


def _params(name, arguments):
    """A minimal MCP tools/call params object."""
    return {"name": name, "arguments": arguments}


def _wire(params):
    """Force a JSON transport round-trip: plain data end to end."""
    return json.loads(json.dumps(params))


def test_x01_envelope_round_trip_allows(world):
    params = _params("search", {"q": "acme"})
    attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
    # Envelope rides in params._meta under exactly the extension key, no new
    # top-level fields (draft §2).
    assert set(params["_meta"][EXTENSION_ID]) == {"chain", "invocation"}
    assert "chain" not in params and "invocation" not in params
    d = guard_request(_wire(params), world["resolver"], Policy(), TOOL_SERVER)
    assert d.allowed, d


def test_x02_over_scope_tool_denied_maps_to_31000(world):
    params = _params("drop_tables", {"db": "prod"})
    attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
    d = guard_request(_wire(params), world["resolver"], Policy(), TOOL_SERVER)
    assert not d.allowed and d.error == ERR_TOOL_NOT_GRANTED
    err = denial_to_jsonrpc_error(d, 7)
    assert err["jsonrpc"] == "2.0" and err["id"] == 7
    assert err["error"]["code"] == OLINOOL_DENIED_CODE == -31000
    # Closed ERR_* rides in data.error, untouched (draft §3).
    assert err["error"]["data"]["error"] == ERR_TOOL_NOT_GRANTED


def test_x03_missing_meta_is_structure_not_scope(world):
    # Guarded tool, but the client shipped no olinool envelope: fail closed with
    # ERR_STRUCTURE — absence of artifacts is not a scope decision (draft §3).
    params = _params("search", {"q": "acme"})
    d = guard_request(_wire(params), world["resolver"], Policy(), TOOL_SERVER)
    assert not d.allowed and d.error == ERR_STRUCTURE
    err = denial_to_jsonrpc_error(d, 1)
    assert err["error"]["code"] == -31000
    assert err["error"]["data"]["error"] == ERR_STRUCTURE


def test_x04_forged_chain_denied_is_olinool_not_oauth(world):
    # A tampered/forged receipt dies inside olinool verification and surfaces as
    # a JSON-RPC -31000 error — NOT an HTTP 401. The two layers are distinct
    # (draft §3): a bearer token could be perfectly valid while the delegation
    # chain is forged.
    params = _params("search", {"q": "acme"})
    attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
    params = _wire(params)
    leaf = params["_meta"][EXTENSION_ID]["chain"][-1]
    forged = leaf[:-2] + ("A" if leaf[-1] != "A" else "B")  # flip a signature byte
    params["_meta"][EXTENSION_ID]["chain"][-1] = forged
    d = guard_request(params, world["resolver"], Policy(), TOOL_SERVER)
    assert not d.allowed
    err = denial_to_jsonrpc_error(d, 9)
    assert err["error"]["code"] == -31000            # olinool's code
    assert "error" in err and "status" not in err    # a JSON-RPC error, no HTTP status


def test_x05_statelessness_two_independent_calls(world):
    # Each request is self-contained (draft §2): two separate verifier instances
    # (separate Policy = separate nonce cache) with NO shared state both allow.
    for q in ("first", "second"):
        params = _params("search", {"q": q})
        attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
        d = guard_request(_wire(params), world["resolver"], Policy(), TOOL_SERVER)
        assert d.allowed, (q, d)


def test_x06_replay_second_call_denied(world):
    # The one piece of receiver state is the R12 nonce cache: replay the SAME
    # invocation against ONE policy instance and the second is denied.
    pol = Policy()
    params = _params("search", {"q": "x"})
    attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
    wired = _wire(params)
    assert guard_request(wired, world["resolver"], pol, TOOL_SERVER).allowed
    d = guard_request(wired, world["resolver"], pol, TOOL_SERVER)
    assert not d.allowed
    err = denial_to_jsonrpc_error(d, 2)
    assert err["error"]["code"] == -31000


def test_x07_allowed_decision_has_no_error_object(world):
    params = _params("search", {"q": "acme"})
    attach_envelope(params, world["chain"], world["agent"], TOOL_SERVER)
    d = guard_request(_wire(params), world["resolver"], Policy(), TOOL_SERVER)
    assert d.allowed
    with pytest.raises(ValueError):
        denial_to_jsonrpc_error(d, 1)  # never mint a denial for a passing call
