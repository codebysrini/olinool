# moolam

**The shared root layer of the olinool agent-governance stack: Ed25519
identities, key resolution, RFC 8785 canonical encoding, and compact JWS.**

*Moolam* (Tamil: மூலம், "root/source") is the layer every seal presses on.
It exists as its own package because [olinool](https://pypi.org/project/olinool/)
(delegation receipts) and its sibling transports share one crypto root: a single
implementation of canonicalization and signing whose bytes are certified
byte-for-byte against an independent TypeScript verifier. Three drifting copies
would silently break that cross-verifier conformance, so there is exactly one.

- **Ed25519 only, by policy** — no algorithm negotiation, none accepted.
  Post-quantum migration is a versioned-profile bump later, not an option flag.
- **Strict RFC 8785 (JCS)** canonical JSON via the `rfc8785` package, with
  known-answer vectors.
- **Compact JWS** mint/verify with closed error codes.
- **Key resolution seam** — a `KeyResolver` interface; bring your own directory
  (agent cards, `.well-known`, static registry).

Most users want `pip install olinool` (which pins `moolam==0.1.0` exactly);
install moolam directly only to build your own artifact format on the same
certified root.

License: Apache-2.0. Part of the olinool-stack repository.
