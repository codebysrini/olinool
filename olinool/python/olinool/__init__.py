"""olinool — proof-carrying delegation receipts for agent-to-agent calls.

Olinool (Tamil: oli "light" + nool "thread") is the luminous thread through
every microabode in Mamuni Mayan's Aintiram tradition — the axis that carries
order through a structure. Here, the receipt chain is that thread: break it
at any hop and the light does not reach the leaf.

Naming system (locked 2026-07-02):
    olinool  — the library and the receipt chain (thread of light)
    muthirai — mint/attenuate module: the seal pressed at each delegation
    ayadi    — verification + conformance: the pre-trust check
    vinkaru  — the root receipt / trust anchor (the seed of space)
    moolam   — the shared root-layer package (crypto, keys, canonical encoding)

Public surface (v0):
    Signer, KeyResolver            — identity + key discovery seam
    mint_root, attenuate           — issue receipts (muthirai)
    invoke                         — bind a request to a receipt (PoP)
    verify_chain, verify_invocation, Policy, Decision  (ayadi)
    mint_result, verify_result     — signed outcome records (result, v0.2)
"""
from .errors import Decision, MintError  # noqa: F401
from .invocation import invoke  # noqa: F401
from .keys import KeyResolver, Signer  # noqa: F401
from .muthirai import attenuate, jws_decode, mint_root, receipt_hash  # noqa: F401
from .result import mint_result, verify_result  # noqa: F401
from .scopes import grant_permits, is_subset  # noqa: F401
from .ayadi import Policy, verify_chain, verify_invocation  # noqa: F401

__version__ = "0.1.0"
