# olinool

**Delegation receipts for agent-to-agent and agent-to-tool calls: offline-verifiable scope attenuation, proof-of-possession, and a negotiable integrity ladder — with an adversarial conformance corpus as a first-class artifact.**

*Olinool* (Tamil: ஒளி நூல், *oli* "light" + *nool* "thread") is the luminous thread that carries order through every structure in Mamuni Mayan's Aintiram tradition. Here, the receipt chain is that thread: each delegation hop presses a **muthirai** (seal) onto a new receipt; the chain roots in a **vinkaru** (seed receipt) minted by the human or org principal, all pressed on the **moolam** root layer; every receiver runs **ayadi** (the pre-trust verification) locally in ~0.05 ms/hop. Break the thread anywhere — forged seal, widened scope, spliced parent — and the light doesn't reach the leaf. No gateway, no central log.

Status: v0.3 prototype (profile split + `sd-1` shipped). 54/54 tests (adversarial suite + profile/result/byte-identity oracles), 22/22 conformance vectors certified identically by both verifiers, Python reference implementation + certified TypeScript verifier. Public API is plain English (`mint_root`, `attenuate`, `invoke`, `verify_invocation`, `mint_result`, `verify_result`); the Tamil names attach to modules and concepts.

## Prior art, honestly

olinool stands on [UCAN](https://github.com/ucan-wg/spec) (proof-carrying delegation + invocation receipts), [Biscuit](https://www.biscuitsec.org/) (offline attenuation), and arrives after [AIP](https://www.ietf.org/archive/id/draft-prakash-aip-00.html) (invocation-bound capability tokens for MCP/A2A) and alongside [cA2A](https://github.com/agentrust-io/ca2a) (attested, attenuated delegation as a TEE-rooted profile on A2A — the confidential-computing take on the same idea; olinool's L0 is deliberately software-only and verifies in ~0.05 ms/hop with no enclave). What olinool adds: per-hop receipt portability (independent archival; selective disclosure via the implemented `sd-1` SD-JWT profile, SPEC §16), an attestation slot on every hop (L0 software / L1 TEE-EAT / L2 chained — L1+ reserved, not shipped), and a format-neutral adversarial conformance corpus. An AIP bridge is planned so one verifier serves both formats. If you need Datalog policies today, use Biscuit/AIP; if you need a gateway with instant revocation, run the same verifier at a proxy (gateway profile) — this library will tell you so rather than pretend.

## Quickstart

```python
from olinool import Signer, KeyResolver, mint_root, attenuate, invoke, verify_invocation, Policy

principal = Signer.generate("did:web:acme.example")
orch      = Signer.generate("did:web:acme.example:orchestrator")
worker    = Signer.generate("did:web:vendor.example:worker")

resolver = KeyResolver()
for s in (principal, orch, worker): resolver.register_signer(s)

# vinkaru — the root receipt (principal → first agent)
r0 = mint_root(principal, orch.agent_id,
               scope=[{"act": "read", "res": "datasets/*", "limits": {"amount": 50}}],
               ttl_s=3600, max_depth=3)
# muthirai — seal a narrowed delegation onto the thread
r1 = attenuate(r0, orch, worker.agent_id,
               scope=[{"act": "read", "res": "datasets/eu-*", "limits": {"amount": 10}}])

req = b'{"method":"GET","path":"/datasets/eu-42"}'
inv = invoke(r1, worker, "did:web:data.example", req)   # proof-of-possession

# ayadi — receiver-side verification, fully offline
decision = verify_invocation([r0, r1], inv, req, "did:web:data.example", resolver, Policy())
assert decision.allowed
```

## Layout

```
SPEC.md              wire format + verification rules R1–R12 (matches the code)
python/olinool/      reference implementation (Ed25519 via `cryptography`)
  muthirai.py          mint / attenuate — the seal at each hop
  ayadi.py             chain + invocation verification (R1–R12)
  invocation.py        proof-of-possession artifact
  scopes.py            the scope algebra (subset relation)
  keys.py, core.py     thin shims over the moolam root layer
python/tests/        adversarial suite: forgery, splicing, truncation, replay,
                     depth inflation, stolen chains, widened limits, assurance floors
python/olinool/conformance/vectors/
                     language-neutral JSON vectors (keys inline, self-contained;
                     shipped in the wheel — `python -m olinool.conformance`)
conformance/         ayadi corpus generator + runner; certify ANY impl by exit code
```

Run: `pip install cryptography pytest && python -m pytest python/tests/ -q && python conformance/run.py`

## What this does not solve (read before depending on it)

Cumulative budgets across parallel chain uses (needs a shared counter). Instant universal revocation offline (TTL + epoch bounds the risk; gateway/central-mint profile exists for hard revocation). Full upstream chain privacy (the implemented `sd-1` profile, SPEC §16, narrows it: non-linkage claims — `rid`, `asr.evidence`, display metadata — ride holder-withholdable salted-hash disclosures and an auditor can confirm linkage while seeing nothing else, but a full-verifying receiver still sees upstream `sub`/`scope` because R4/R6 re-verify them; ZK subset proofs are a research track, out of scope). In-scope misbehavior (a correctly-authorized agent doing something dumb is a guardrail problem — see ACS runtime policies, mech-gov-style decision governance).

## Roadmap

v0.2 — shipped: `olinool-result` outcome records (SPEC §14, corpus r01–r03), strict RFC 8785 JCS (moolam), single-agent middleware wedge (`olinool-mcp/`), TypeScript verifier certified 11/11 against the corpus (`typescript/`). Remaining: AIP bridge + bridge vectors.
v0.3 — shipped (2026-07-07): profile/data-model split (SPEC §15) and the `sd-1` selective-disclosure chain profile (SPEC §16; Python mint+verify, TS verify, corpus 20/20 in both) — narrows chain privacy to non-linkage claims plus auditor-side disclosure; upstream `sub`/`scope` remain visible to full-verifying receivers (SPEC §16.5). Remaining: L1 attestation (Nitro, EAT evidence), framework middleware for two agent SDKs.

License: Apache-2.0.
