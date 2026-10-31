"""olinool-mcp wedge — valid call, over-scope tool, replay, wrong receiver,
tampered arguments. Every guarantee here is olinool's; the wedge only binds
the tool-call shape to it, so each test maps to an ayadi rule or the pinned
tool→grant convention."""
from __future__ import annotations

import json

import pytest

from olinool import KeyResolver, Policy, Signer, mint_root
from olinool.errors import ERR_AUDIENCE, ERR_POP, ERR_REPLAY
from olinool_mcp import ERR_TOOL_NOT_GRANTED, guard, wrap_call

TOOL_SERVER = "did:web:tools.example"


@pytest.fixture
def world():
    principal = Signer.generate("did:web:acme.example")
    agent = Signer.generate("did:web:acme.example:assistant")
    resolver = KeyResolver()
    for s in (principal, agent):
        resolver.register_signer(s)
    # The single-agent pattern: one root receipt, no onward delegation.
    r0 = mint_root(principal, agent.agent_id,
                   scope=[{"act": "call", "res": "tool/search*"}],
                   ttl_s=600, max_depth=0)
    return dict(agent=agent, resolver=resolver, chain=[r0])


def test_m01_valid_call_allowed(world):
    env = wrap_call(world["chain"], world["agent"], TOOL_SERVER, "search", {"q": "acme"})
    env = json.loads(json.dumps(env))  # transport round-trip: plain data end to end
    d = guard(env, world["resolver"], Policy(), TOOL_SERVER)
    assert d.allowed, d


def test_m02_over_scope_tool_rejected(world):
    env = wrap_call(world["chain"], world["agent"], TOOL_SERVER, "drop_tables", {"db": "prod"})
    d = guard(env, world["resolver"], Policy(), TOOL_SERVER)
    assert not d.allowed and d.error == ERR_TOOL_NOT_GRANTED


def test_m03_replayed_envelope_rejected(world):
    pol = Policy()  # one receiver-side policy = one replay cache
    env = wrap_call(world["chain"], world["agent"], TOOL_SERVER, "search", {"q": "x"})
    assert guard(env, world["resolver"], pol, TOOL_SERVER).allowed
    d = guard(env, world["resolver"], pol, TOOL_SERVER)
    assert not d.allowed and d.error == ERR_REPLAY


def test_m04_wrong_receiver_rejected(world):
    env = wrap_call(world["chain"], world["agent"], TOOL_SERVER, "search", {"q": "x"})
    d = guard(env, world["resolver"], Policy(), "did:web:other.example")
    assert not d.allowed and d.error == ERR_AUDIENCE


def test_m05_tampered_arguments_rejected(world):
    env = wrap_call(world["chain"], world["agent"], TOOL_SERVER, "search", {"q": "public data"})
    env["arguments"]["q"] = "salary table"  # args edited after signing
    d = guard(env, world["resolver"], Policy(), TOOL_SERVER)
    assert not d.allowed and d.error == ERR_POP
