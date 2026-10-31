# dabba V1 / seal-path audit — 2026-07-02 (Fable-5 review)

Scope: `views.py`, `station.py`, `model.py`, `test_dabba.py`. Question: is the scoped-view guarantee (V1) real, and is the seal chain sound?

## Verdict: sound. Two honest limitations to document; no code changes required.

**What holds (verified by reading + the 14-test suite):**
- `build_view` enforces V1 **by construction**: deny-by-default deps (`deps.get(hop, [])` → empty), bounds check, and earlier-tier-only check (`idx >= hop` raises). Non-declared tiers cannot enter a view — test_d08 proves a poisoned planner tier is invisible to a summarizer that didn't declare it.
- Seal chain matches SPEC S1–S8: tier-hash (d02), prev-link (d03), foreign-writer (d04), route (d05), expiry (d06), and the Lid-core binding (d10–d12) that catches `deps`/`ttl`/`goal` mutation after sealing. The `gov` exclusion (d13) correctly lets the olinool bridge pin a receipt chain post-hoc.
- test_d07 already documents honestly: poison **inside a declared dependency** is NOT stripped — V1 protects against non-input tiers leaking, not against a dependency you chose to read being dirty.

**Limitation A — the `instruction` parameter is caller-supplied and unpoliced.** `build_view(dabba, hop, instruction)` places `instruction` verbatim into the view. If an orchestrator builds that string by concatenating upstream tier content, leakage happens *upstream* of the module V1 protects. V1 guarantees build_view adds nothing; it cannot guarantee the caller's instruction is a clean routing directive. **Mitigation:** treat `instruction` as routing metadata only; never assemble it from other agents' outputs. The dap-bench dabba runtime (below) obeys this — the summarizer's instruction is a fixed string, and its only data input is the declared collector tier.

**Limitation B — seals commit to produced tiers, not to the view shown.** A seal binds the tier an agent *output*, plus the Lid core. It does not bind W(k), the context the agent was *given*. So V1 is a **runtime property of a trusted Station**, not a fact independently provable from the sealed Dabba afterward. If you don't trust the Station that built the views, the seals alone don't prove scoped delivery happened. For in-process v0 (single trusted Station) this is fine and mirrors olinool's honesty about "enforcement depends on the verifier actually verifying." A future profile could bind `sha256(view)` into each seal to make V1 post-hoc auditable — noted for the roadmap, out of scope for v0.

Neither limitation blocks the benchmark rewire or v0; both belong in dabba/SPEC §12 (known gaps) before any public claim that dabba "proves" scoped delivery — the defensible word is "enforces (under a trusted Station)."
