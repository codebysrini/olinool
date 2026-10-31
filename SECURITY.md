# Security Policy

## Reporting

Report privately through GitHub (Security tab → "Report a vulnerability") or by email to codebysrini@gmail.com; do not open public issues for vulnerabilities. This is a pre-1.0 research prototype — no security guarantees.

## Threat model (v0.1, enforced & tested)

Forged/spliced/reassembled delegation chains, scope widening (incl. dropped ceilings), stolen/replayed/truncated chains, cross-agent view leakage, depth inflation by collusion. See package SPECs and conformance corpora.

## Known limitations (NOT solved — do not rely on)

Instant offline revocation; cumulative budget enforcement; upstream `sub`/`scope` privacy against full-verifying receivers — the implemented `sd-1` selective-disclosure profile (olinool SPEC §16) narrows the leak, not closes it: non-linkage claims (`asr.evidence`, display metadata; `rid` from parties not running full verification) can be withheld and an auditor can confirm linkage while learning nothing else, but R4/R6 re-verification reads upstream `sub`/`scope`, so full chain-content privacy is NOT provided (zero-knowledge subset proofs: research track, out of scope); L1/L2 hardware attestation (format slot only). dabba enforces scoped delivery under a *trusted* Station; it does not prove it post-hoc.
