# The Olinool Stack

**Governed, context-minimal agent-to-agent work: delegation receipts that prove authority, a task-state runtime that proves action, and the benchmark that justified building it.**

Every handoff between agents carries a sealed receipt whose scope can only shrink (olinool); every task travels as a sealed, append-only packet where each agent sees only its slice (dabba); both press their seals on one shared crypto root (moolam); and the central claims are backed by an adversarial benchmark with a pre-committed decision gate (dap-bench). Names come from Mamuni Mayan's Aintiram tradition (see [Names](#names)); the project's working principles are in [AINTIRAM.md](AINTIRAM.md).

## Packages

| Package | What it is | Status |
|---|---|---|
| [`moolam/`](moolam/) | Root layer: Ed25519, key resolution, RFC 8785 canonical JSON, compact JWS | 7/7 tests |
| [`olinool/`](olinool/) | Delegation receipts: offline-verifiable scope attenuation, proof-of-possession, signed result records, selective-disclosure profile (`sd-1`), assurance ladder, conformance corpus | 54/54 tests · 22/22 vectors |
| [`olinool-mcp/`](olinool-mcp/) | Single-agent wedge: signed, scoped, replay-proof tool calls (mint-on-egress / verify-on-ingress middleware; transport-agnostic) | 12/12 tests |
| [`dabba/`](dabba/) | DAP transport v0: Lid/Tiers/seal chain, scoped views W(k), in-process Station, olinool bridge | 21/21 tests · 13/13 vectors |
| [`dap-bench/`](dap-bench/) | Scoped-view vs full-history benchmark, injection probe, cross-backend gate | Verdict: **BUILD** — held end-to-end |
| [`typescript/`](typescript/) | Second-language ayadi verifier (R1–R12 + result records + `sd-1`) proving the corpus is format-neutral | 22/22 vectors certified |

Headline numbers (local qwen2.5:3b, through the real Station): **1.83×** less input context end-to-end (**11.5×** at the scoped hop), **1.3×** faster end-to-end, quality parity or better, injections **4/4 blocked** architecturally with **12/12** seal chains verified after execution. Full method log, including every scoring bug found and fixed: [`dap-bench/README.md`](dap-bench/README.md).

## Install

```bash
pip install olinool              # also installs moolam, the shared crypto root
python -m olinool.conformance    # certify the installed wheel against the shipped corpus (22/22)
```

`moolam` and `olinool` are released to PyPI from this repository by tag (`moolam-v*`, `olinool-v*`) through Trusted Publishing, with PEP 740 attestations. `dabba`, `olinool-mcp`, `dap-bench`, and the TypeScript verifier are source-only.

## Verify everything locally

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install cryptography rfc8785 pytest
(cd moolam  && python -m pytest python/tests -q)
(cd olinool && python -m pytest python/tests -q && python conformance/run.py)
(cd olinool-mcp && python -m pytest python/tests -q)
(cd dabba   && python -m pytest python/tests -q && python conformance/run.py corpus/)
(cd dap-bench && python run.py --backend mock --n 12 --runtime dabba)
```

No package installs required — conftests bootstrap sibling paths. The stack's only third-party dependencies are `cryptography` and `rfc8785` (strict RFC 8785 JCS, in moolam since v0.2).

## Documents

In-repo documentation is deliberately minimal: each package's `SPEC.md` and `README.md`, `dabba/AUDIT_views_2026-07-02.md` (referenced by dabba's SPEC §7), and `dap-bench/README.md` (the method log that makes the results interpretable). Design history and strategy notes are maintained privately outside this repository.

## Honesty ledger, short form

Claimed nowhere: instant offline revocation, cumulative budget enforcement, full chain privacy (the implemented `sd-1` profile narrows it — non-linkage claims hidden behind salted-hash disclosures, auditor-side selective disclosure — but upstream `sub`/`scope` stay visible to full-verifying receivers; `olinool/SPEC.md` §16.5), L1/L2 attestation (slot reserved, unbuilt), or that dabba "proves" scoped delivery — it *enforces* it under a trusted Station (see `dabba/SPEC.md` §7). What is claimed is tested, and the conformance corpora are the proof anyone can run.

## Names

Concepts get exactly one name, locked before code exists:

- **olinool**: the receipt-chain library and the chain concept ("thread of light")
- **muthirai**: the seal concept; olinool's mint/attenuate module (`olinool/python/olinool/muthirai.py`)
- **ayadi**: verification and conformance
- **moolam**: the shared root layer (Ed25519 identities, key resolution, canonical encoding, JWS) that olinool and dabba both build on
- **vinkaru**: the root receipt / trust anchor

Public APIs stay descriptive English (`mint_root`, `attenuate`, `verify_invocation`, …); the Tamil names attach to modules and concepts.

## License

Apache-2.0 (see [LICENSE](LICENSE)). To report a vulnerability, see [SECURITY.md](SECURITY.md).
