"""olinool.keys — re-exports the identity/key-resolution seam from moolam.

The Signer / KeyResolver implementation is shared across the stack; this thin
module preserves `from .keys import ...` imports within olinool.
"""
from moolam.keys import KeyResolver, Signer  # noqa: F401
