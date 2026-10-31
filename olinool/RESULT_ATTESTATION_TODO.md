# Deferred spec task — result attestation taxonomy (before §5a MCP wiring)

**Status:** DEFERRED by decision 2026-07-04 (Srini + advisor). The MCP extension ships its guard carriage WITHOUT result records; §5a is reserved pending this spec. SPEC-before-implementation (AINTIRAM): freeze the taxonomy + verify rules + vectors here, THEN wire transport.

## Why deferred (the finding that triggered it)

§5a of `olinool-mcp/EXTENSION_DRAFT.md` proposed a server-attached result under `ver:"counter"`. Two problems surfaced:

1. **Name collision with AIP.** AIP (draft-prakash-aip, our bridge neighbor) defines: L1 self-reported, **L2 counter-signed = the DELEGATOR verifies and co-signs**, L3 third-party attested. §5a used "counter" for the SERVER/EXECUTOR — a different actor. Shipping this mis-reads to anyone who knows AIP.
2. **Conflated roles.** There are THREE distinct attestation roles, not two:
   - **self** — the leaf *subject* attests its own output. `actor == leaf.sub`. EXISTS today (`olinool-result`, `ver:"self"`).
   - **delegated-countersign** — a *parent in the chain* (delegator) independently verifies a descendant's output and co-signs. Actor is an in-chain issuer. (AIP's real "counter".)
   - **receiver-attested** — the *receiver/executor* (e.g. the MCP server) attests "I received invocation X from subject S and executed it, output hash H." **The receiver is NOT in the delegation chain** — no receipt, key resolved out-of-band via receiver_id. This is what the MCP server case actually needs, and it is the EU AI Act Art. 12 action-log shape.

## What the spec must define (each of the two new lanes)

For `delegated-countersign` and `receiver-attested`:
- **Signer + key resolution:** who signs, how their key is found (in-chain issuer key vs. out-of-band receiver did).
- **Bindings:** `rcp` (leaf receipt hash), `inv` (invocation hash), `out` (output sha256), plus for delegated-countersign a link to the attesting hop.
- **Verify rules:** new named rules; the receiver-attested lane explicitly does NOT require the signer to be `leaf.sub` (that inversion is the whole point) but DOES require the signer to be the invocation's `aud`/receiver for receiver-attested, or an ancestor issuer for delegated-countersign.
- **Closed-error additions:** e.g. `ERR_RESULT_SIGNER` for signer-role mismatch. Keep the set closed.
- **Corpus vectors:** valid + adversarial (wrong signer role, unbound receipt, forged out-hash) for each lane, mirroring the r0x result vectors.
- **`mint_result` refactor:** `mint_result` currently guards `actor == leaf.sub`. Generalize to `mint_result(..., ver=...)` dispatching per lane, each with its own guard — do NOT just remove the check.

## Naming (propose to Srini before freezing)
Candidate `ver` values: `"self"` (keep), `"delegated"` (or `"parent-countersign"`), `"receiver"` (or `"executor-attested"`). Avoid bare `"counter"` (collision). One concept, one name (AINTIRAM MURAI).

## Only after this is frozen
Wire `olinool-mcp/mcp_ext.py` to attach the `receiver`-lane result into `_meta` on the response (EXTENSION_DRAFT §5a), with tests.
