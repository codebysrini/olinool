"""moolam (மூலம், "root / source") — the root layer of the olinool stack.

In Mamuni Mayan's system the Moolam is the primal dot at the center of the
grid: the source everything else emanates from. Here it is the dependency
root everything presses seals on: Ed25519 identities, key resolution,
canonical encoding, hashing, and compact-JWS sign/decode. No policy lives
here — no scopes, no receipts, no tiers. Depends only on `cryptography`.

    pip install moolam          # this package alone
    pip install olinool         # governance receipts — pulls moolam
    pip install dabba           # task state / scoped views — pulls moolam

Naming registry (locked): olinool = receipt chain (thread of light) ·
muthirai = the seal concept, olinool's mint module · ayadi = verification ·
moolam = this root layer · vinkaru = root receipt / trust anchor.
"""
from .core import b64u_decode, b64u_encode, canonical_json, sha256_b64u  # noqa: F401
from .jws import jws_decode, jws_sign  # noqa: F401
from .keys import KeyResolver, Signer  # noqa: F401

__version__ = "0.1.0"
