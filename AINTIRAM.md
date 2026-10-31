# AINTIRAM — the five-fold order of the olinool stack
### The constitution. When any session — human or model — hits a conflict between a plan and a principle, this file wins. Read it before extending anything.

**How to use this file:** it is consulted, not admired. Precedence in any conflict: §1 Purpose > §2 Five-fold invariants > data-model semantics (SPECs) > encoding profiles > SDKs > features. If your plan violates a lower layer, redesign the plan. If it violates §1 or §2, STOP and surface the conflict to Srini — do not reinterpret, do not "improve" the principle. Amendments: only with (a) new evidence or a fired falsifier, (b) Srini's explicit sign-off, (c) an entry in §7.

Named for Mamuni Mayan's Aintiram: the five-fold process by which the Unmanifest source becomes ordered form through SPACE, TIME, LIGHT, and SOUND — "the transformation of disorderly Om Light and Om Sound into orderliness." That is literally this project: untrusted, chaotic agent activity transformed into verifiable order. The metaphor is load-bearing, not decorative.

---

## 1. MOOLAM — the Source (the purpose that everything derives from)

> **Work flows freely between agents; authority and proof must flow with it — verifiable by anyone, owned by no one.**

Every artifact in this stack exists to answer three questions offline: *who allowed this* (authority), *was it narrowed properly* (attenuation), *what was actually done* (action). A feature that does not shorten the path to one of those answers for a real person — a platform engineer passing security review, a compliance officer with an auditor, a tool author wanting safe calls in five lines, a researcher certifying an implementation — does not ship. "Ahead of protocol X" is never a reason; "beneath whichever protocol wins" is the position.

## 2. The Five-fold Order (inviolable invariants, each with its enforcement)

**VELI — SPACE (boundary).** Authority and context exist only within explicit, bounded space, and child space is always contained in parent space.
- Scope may only narrow along a chain; dropping a ceiling is widening. *(R6; tests c02–c04; vector v02)*
- Each hop sees only its declared slice — view W(k) contains nothing beyond Lid, instruction, declared inputs. *(V1; dabba v08; CaMeL lineage)*
- You act only where named: audience and receiver binding. *(R11)*
- **No ambient authority, ever**: nothing is permitted because of where code runs, what network it sits on, or what a config file implies. Authority arrives inside a signed artifact or it does not exist. *(object-capability principle; R3/R4)*

**KAALAM — TIME (the clock is a security mechanism).** Nothing is valid forever; time bounds are load-bearing, not metadata.
- Windows nest: no child outlives its parent. *(R7)*
- Short life beats revocation infrastructure; expiry is the default kill-switch, epochs and feeds are additions. *(SPEC §12; AIP takes the same stance)*
- Freshness and single-use at the moment of action: invocation TTL + nonce. *(R12; c13)*

**OLI — LIGHT (the thread of visibility).** Authority is a chain of light: visible, traceable, verifiable by anyone, needing no central log or gateway.
- Every link is signed, hash-bound to its parent, and issuer-continuous; break the thread anywhere and the light does not reach the leaf. *(R2, R4, R5; c05–c07)*
- Verification is offline and local; the verifier is CONSENSUS-CRITICAL — two certified implementations disagreeing on one vector is a security incident, not a bug. *(corpus law; TS certification)*
- Fail closed, and say why in a closed error vocabulary. *(closed ERR_* sets)*

**OOSAI — SOUND (the act, spoken once).** Doing is distinct from being allowed to do, and both leave evidence.
- Possession, not observation: a chain is exercised only by the named holder's key, bound to the exact request, at the named receiver, once. *(R12; c11–c15)*
- Every act may answer for itself afterward: signed results link authority to outcome. *(olinool-result; dabba seals)*
- **Control is never assembled from data**: instructions are routing metadata from trusted callers; tier/tool/document content never becomes instruction. *(dabba Limitation A; CaMeL's control/data-flow separation)*

**MURAI — ORDER (the law of the process itself).** The transformation from disorder to order is monotonic, append-only, and closed.
- History is append-only and sealed; nothing is rewritten. *(S-rules; frozen results/evidence files)*
- Closed sets, pinned profiles, **no in-band negotiation of anything** — algorithms, formats, versions. Downgrade must be structurally impossible, not discouraged. *(c20 doctrine; horizon §2B)*
- Frozen corpora are wire-format law; generators add, never rewrite. *(corpus law)*
- Names are locked before code exists; concepts get exactly one name. *(naming registry: README.md)*

## 3. The Primitives (the irreducible vocabulary)

Nouns: **Key** (identity), **Seal** (signature — muthirai), **Receipt** (delegated authority; root = vinkaru), **Invocation** (proof of possession for one act), **Result** (signed outcome), **Tier** (append-only state entry), **View W(k)** (scoped slice), **Thread** (the chain — olinool), **Vector** (conformance case), **Ledger** (certification record), **Registry** (locked names/claims).
Verbs: **mint, attenuate, invoke, verify, seal, record, certify**.

The rule: every new feature must be expressible as a composition of these. If it cannot be, it is either out of scope or an amendment to this file — never a quiet addition. (Extension data rides in namespaced `ext.*` claims; it never changes verification semantics.)

**Admission test for a new primitive** (adapted from Srinivasan, *The Building Blocks That Outlive Your Agent Framework*, 2026): (1) Is it a noun — an artifact or capability — rather than a verb — routing/orchestration? (2) Can its contract be stated without referencing any model, framework, or transport? (3) Does it compose with the existing primitives without a mediator? Three yeses → candidate primitive, invest deeply. Any no → implementation detail: keep it thin, replaceable, and out of this file. Corollary — the **reversibility test**: remove the addition; if the core does not survive intact, orchestration has leaked into the primitives.

## 4. The Primal Instincts (quick reference — the gut checks)

1. No ambient authority. 2. Authority only narrows. 3. Evidence over assertion — every public claim is TESTED, SOURCE-backed, or labeled DESIGN/ROADMAP. 4. Verify at the door, not on the road — receivers verify; gateways are deployments, not dependencies. 5. Each hop sees only its slice. 6. Never build control flow from data. 7. The clock is a security mechanism. 8. Possession, not observation. 9. Closed sets; no negotiation. 10. Append-only; freeze the corpus. 11. Fail closed with a named reason. 12. Nouns over verbs: invest in artifacts (receipts, seals, views, results); keep transports, routing, and orchestration thin and replaceable — ride substrates, never build roads. 13. Lead with weaknesses — the honesty ledger is the moat. 14. A verifier disagreement between languages is a security hole. 15. Autonomy never outpaces evidence: expanding what an agent may do without asking is a policy change gated on measured primitive quality — receipts and results are the metric that justifies each gate, and "it seems reliable" justifies nothing. 16. Transitions are metrics, not feelings: every stage, gate, version, and architecture change must be answerable with a test-suite result (pre-committed, like dap-bench's gates and the Rust-core trigger).

## 5. Threat anchoring (why these instincts, in the industry's language)

OWASP Agentic Top 10 (2026): **ASI03** Agent Identity & Privilege Abuse ↔ instincts 1, 2, 8 (receipts + PoP). **ASI01** Goal Hijack and **ASI06** Memory/Context Poisoning ↔ instincts 5, 6 (scoped views; control/data separation — measured: 4/4 hijacks in full-context vs 0/4 scoped, dap-bench). **ASI02** Tool Misuse ↔ instinct 4 (guard at ingress). What this stack deliberately does NOT solve: in-scope misbehavior, cumulative budgets, instant offline revocation — see SECURITY.md; claiming otherwise violates instinct 13.

## 6. Lineage (the shoulders; cite, don't re-derive)

The founder's own prior doctrine, absorbed above: nouns over verbs; "prompt-layer access control is not access control — the tool carries the enforcement"; identity propagates through the entire call chain; autonomy gates as policy changes with primitive-quality prerequisites; evals before capabilities; the reversibility test · Object-capability security (no ambient authority, least authority, designation=authorization) · CaMeL, arXiv:2503.18813 (control/data-flow separation + capabilities, provable prompt-injection defense) · UCAN / Biscuit / Macaroons (attenuated delegation lineage) · IETF: WIMSE WPT (per-request PoP), Transaction Tokens (call-chain context), SD-JWT RFC 9901 (selective disclosure), draft-niyikiza-oauth-attenuating-agent-tokens (structural monotonicity — convergent with our scope algebra) · AIP draft-prakash-aip-00 (nearest neighbor; bridge, don't fight) · EU AI Act Art. 12 (tamper-evident action logging — the regulatory pull) · The five-fold order: Mamuni Mayan's Aintiram via V. Ganapati Sthapati's tradition.

## 7. Amendment log

- 2026-08-04 — §6 lineage: the founder's self-citation removed entirely (doctrine text retained, unattributed to any external venue). Ratified by: Srini.

- 2026-07-04 — v1 of this constitution. Ratified by: Srini (pending review). Derived from: the July 2026 teardown, dap-bench evidence, v0.1/v0.2 test law, horizon-2030 analysis.
- 2026-07-04 — v1.1: incorporated the founder's published doctrine (Srinivasan 2026) after reading the full article — primitive admission test + reversibility test (§3), instincts 12 (nouns-over-verbs phrasing), 15 (autonomy never outpaces evidence), 16 (transitions are metrics); §6 citation corrected from secondhand distillation to the source. Ratified by: Srini (pending review).
- 2026-07-06 — v1.2: **dap-bench gate split into three panels** (architecture verdict / economics / model-robustness). **Disclosure (mandatory, anti-goalpost):** as originally coded, `compare.py` ran one verdict over every real backend and on 2026-07-06 returned **DO NOT BUILD** — a T2 economics model (`llama-4-scout`) obeyed an injection end-to-end (G3) and `gpt-oss-120b` regressed quality (G2). The panel separation was ratified **after** that result, on the reasoning: *an economics run measures cost/latency/quality across models and was never commissioned to inform the architecture decision, so it must not be able to veto it.* Only the frozen pre-registered reference probe (ollama + claude-cli) gates BUILD; per-model economics gates rows only; per-model B-injection is always reported, never gating (a model obeying its declared input is a model property, not a transport failure — it is what seal-vh-1 localizes, not prevents). The flip is disclosed in `compare.py`, `results/comparison.md`, and `dap-bench/B3_ECONOMICS_REVIEW_2026-07-06.md`; the gate thresholds (G0–G3) are UNCHANGED. New evidence: the 5-model economics run. Ratified by: Srini + Cowork verification (2026-07-06).
