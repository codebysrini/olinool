# dabba — Portable Task-State with Scoped Views (DAP v0.1)
## Wire-format and verification specification, v0.2-draft

**Status:** working draft; matches the reference implementation in `python/` and the vectors in `corpus/`. v0.2 adds the seal-profile seam (§9) and the `seal-vh-1` profile; §§1–8 describe the `seal-1` profile unchanged and remain frozen.
**Scope of v0:** an **in-process** task-state runtime. It proves the property dap-bench measured — that giving each hop only its scoped view is cheaper, faster, and strips injection vectors — with tamper-evident seals over an append-only history. It is a library, not a server.
**Shared base:** all crypto (Ed25519 identities, key resolution, canonical JWS seal-press) is the `moolam` package. dabba adds no crypto of its own.
**Relationship to olinool:** independent. dabba runs with zero olinool installed. When both are present, the optional bridge (§8) carries an olinool receipt in the Lid and treats each sealed Tier as an olinool outcome record. Neither depends on the other; both depend on moolam.

---

## 1. Model

A task travels as a **Dabba** (Hindi/Marathi: lunchbox — the dabbawala delivery metaphor behind DAP):

> **D = (Lid, Tiers, Seals)**

- **Lid** — the header: `goal`, `route` (ordered agent ids), `ttl`, `deps` (per-hop declared read set — see §2), and an optional `gov` slot (an olinool receipt-chain reference; ∅ without the bridge). The Lid's **core** — `{goal, route, ttl, deps}` — is authenticated: every seal commits to `sha256(canonical(core))`, so no field in it can change after even one hop has sealed (§3, rule S7). `gov` is deliberately outside the core so the bridge may pin it post-hoc.
- **Tiers** — an append-only list of agent outputs. Once written, a Tier is never mutated.
- **Seals** — a hash-linked chain of signatures: seal *i* signs (Tier *i* + hash of seal *i−1* + the Lid-core hash), giving tamper-evidence over the whole history **and its routing/permission header**.

The **Compacted View V** from the original DAP whitepaper is deliberately **out of v0** — embedding-based compaction must first prove it drops no permission/compliance data, and it can't yet. v0 uses only exact scoped slices.

## 2. The scoped working view — the property under test

When agent *k* is handed the Dabba, it does **not** receive the whole thing. It receives:

> **W(k) = (Lid.goal, instruction_k, inputs_k)**

where `instruction_k` is its routing instruction and `inputs_k` is the explicit, declared set of prior-Tier outputs it needs (default: none; the immediately-preceding Tier only if the route declares a data dependency). This is the DAP claim dap-bench validated: downstream hops don't need raw upstream context.

**View invariant V1 (normative, testable):** the serialized bytes of W(k) MUST contain nothing beyond Lid.goal, instruction_k, and the declared inputs_k. No other Tier's content, no other agent's instruction, no seal material. The leakage test (§6) asserts V1 byte-for-byte, including that a planted injection string in a non-input Tier never appears in any other hop's view. V1 is the security value of scoped views, turned from benchmark observation into an enforced rule.

## 3. Seal chain (normative rules S1–S8)

A verifier evaluates in order, returning the FIRST failure (closed error set, §5):

| Rule | Check | Error |
|---|---|---|
| S1 | Dabba parses; Lid has goal/route/ttl; Tiers and Seals equal length | `ERR_STRUCTURE` |
| S2 | each seal is EdDSA, `typ=dabba-seal+jws`, `kid` == the tier's declared writer | `ERR_SIG` |
| S3 | each seal signature verifies against its writer's key (via moolam resolver) | `ERR_SIG` |
| S4 | seal *i* references seal *i−1* by hash (`prev`); seal 0 has `prev=null` | `ERR_SEAL_LINK` |
| S5 | seal *i*'s `tier_hash` == sha256(exact Tier *i* bytes) | `ERR_TIER_HASH` |
| S6 | seal *i*'s `hop` == *i* and Tier *i*'s `hop` == *i*; writer of Tier *i* == `route[i]` | `ERR_ROUTE` |
| S7 | seal *i*'s `lid_hash` == sha256(canonical Lid core) — goal/route/ttl/deps unaltered | `ERR_LID` |
| S8 | not past Lid.ttl (now ± skew) | `ERR_EXPIRED` |

S4+S5 make the history tamper-evident: editing any Tier breaks S5; reordering or splicing breaks S4; a wrong author breaks S6. **S7 is the Lid-integrity rule** and is load-bearing for the whole scoped-view guarantee: `deps` decides what each hop may read (§2 / V1), so if `deps` were unauthenticated a Dabba holder could widen any hop's read access undetected. Binding the Lid core into every seal closes that — a `deps` (or `route`, `ttl`, `goal`) mutation after any hop has sealed fails S7. This is *detection*, not prevention, stated honestly as in the PoC doc.

## 4. Station (the in-process custodian)

The **Station** is a plain object (not a network service in v0) that: holds the Dabba, constructs W(k) per hop enforcing V1, appends each returned Tier with a fresh seal, and exposes `verify()` (S1–S8; plus S0/S9 under `seal-vh-1`, §9). It is the DAP "Sorting Station" reduced to exactly what the benchmark exercised — no SWIM, no discovery, no persistence.

## 5. Error codes

Closed set: `ERR_STRUCTURE, ERR_SIG, ERR_SEAL_LINK, ERR_TIER_HASH, ERR_ROUTE, ERR_LID, ERR_EXPIRED, ERR_VIEW_LEAK`.

v0.2 adds three codes for the profile seam (§9): `ERR_PROFILE_NOT_ALLOWED, ERR_PROFILE_MIXED, ERR_VIEW_HASH`. The set stays closed — these are the complete additions.

## 6. Conformance

`corpus/*.json` are self-contained vectors (keys inline). The leakage vectors carry a canary in a non-input Tier and assert it is absent from every other hop's view (V1 / `ERR_VIEW_LEAK`). Reference: pytest suite + runner, certifiable by exit code, same discipline as olinool's ayadi corpus.

## 7. Known gaps (deliberate, v0.1)

1. In-process only — no network transport, no discovery, no multi-process Station.
2. Compacted View V excluded until lossless-for-compliance is provable.
3. Tamper-*evidence*, not prevention (no confidentiality of Tier contents at rest).
4. Cumulative/global constraints are olinool's concern, not dabba's.
5. **The Lid core is fixed at Dabba creation.** Because every seal commits to it, `route`/`deps` cannot be changed after the first hop seals — so v0 requires the full route and dependency plan up front. Dynamic re-routing (append-only route extension with re-sealing) is a later concern, not a v0 capability.
6. **`gov` is unauthenticated by the seal chain** (excluded from the Lid core so the bridge can pin it post-hoc). This is safe because olinool receipts are self-authenticating: tampering with the `gov` pointer can only reference a different chain that olinool independently accepts or rejects — it cannot forge authority. Stated so no one mistakes it for a hole.
7. **Instruction hygiene is the caller's duty (audit Limitation A) — `seal-1` only.** `build_view` places the caller-supplied `instruction` into W(k) verbatim; V1 guarantees build_view *adds* nothing, but cannot stop an orchestrator from assembling the instruction out of upstream tier content. Instructions MUST be routing metadata only, never concatenations of other agents' outputs. **Closed structurally by the `seal-vh-1` profile (§9.1a)**; `seal-1` Dabbas retain this limitation.
8. **V1 is a runtime property of a trusted Station, not post-hoc provable (audit Limitation B) — `seal-1` only.** Seals bind the tier an agent *produced* plus the Lid core — not the view it was *shown*. From the sealed Dabba alone you cannot later prove scoped delivery occurred; you must trust the Station that ran it. The defensible public claim is therefore "enforces scoped delivery (under a trusted Station)," never "proves." **Closed by the `seal-vh-1` profile (§9.1b), absent Station–agent collusion (§9.2)**; `seal-1` Dabbas retain this limitation. Full analysis: `AUDIT_views_2026-07-02.md`.

## 8. Optional olinool bridge

Active only if `import olinool` succeeds. Adds: (a) Lid.gov carries an olinool receipt-chain reference, so the agent authorized for hop *k* is provable, not assumed; (b) each sealed Tier is emitted as an `olinool-result` outcome record (writer, receipt hash, output hash, status) — the artifact olinool needs before it may claim "self-auditing." The authority chain (olinool) and the action chain (dabba seals) cross-link by hash. Without olinool, none of this loads and dabba is a standalone task-state library.

## 9. Seal profiles (v0.2, normative)

The seal wire format is a **profile**, under the same frozen-profile law as olinool (its SPEC §15): a profile id names an exact byte-level behavior; once released, its bytes and verdicts never change — fixes and extensions ship as a NEW id, never as a mutation of an old one. Selection is by the artifact's own markers, gated by a verifier allow-list; never negotiated with a peer.

| profile id | seal `typ` | Lid core | seal payload |
|---|---|---|---|
| `seal-1` | `dabba-seal+jws` | `{goal, route, ttl, deps}` | `{tier_hash, prev, hop, writer, lid_hash}` |
| `seal-vh-1` | `dabba-seal-vh+jws` | `seal-1` core + `{instructions, profile}` | `seal-1` payload + `{view_hash}` |

`seal-1` is the v0.1 format retroactively named; §§1–8 describe it unchanged and it is FROZEN. Rules common to all profiles:

- **Marker.** A Dabba declares its profile in `Lid.profile`; an absent field means `seal-1`. For `seal-vh-1` the profile id is INSIDE the sealed Lid core, so once one hop has sealed, stripping or swapping it breaks S7 (`ERR_LID`).
- **Gate (rule S0, checked before any seal is opened).** The verifier holds an allow-list of profile ids, default `{"seal-1"}`. A Dabba whose profile is not in the list fails `ERR_PROFILE_NOT_ALLOWED`. Acceptance is by verifier policy only — there is no downgrade path an artifact can trigger.
- **Uniformity.** Every seal's `typ` MUST equal the selected profile's typ. Any deviation — another profile's typ or an unregistered one — fails `ERR_PROFILE_MIXED`: the seal does not carry the profile the Lid declared. (A v0.1 verifier rejected an alien typ as `ERR_STRUCTURE`; v0.2 refines the code. No frozen vector pinned the old code, so no verdict changed.)

### 9.1 `seal-vh-1` — authenticated instructions + attested views

Two changes, closing the two audit limitations (§7 gaps 7–8):

**(a) `instructions` joins the Lid core — closes Limitation A structurally.** The core gains `instructions`, exactly one routing instruction per routed hop (`len(instructions) == len(route)`, else `ERR_STRUCTURE`). `build_view` accepts NO caller-supplied instruction under this profile; `instruction_k := Lid.instructions[k]`. Because the core is fixed at Dabba creation and bound into every seal (S7), the instruction channel is sealed **before any tier exists** — an orchestrator cannot assemble an instruction from upstream tier content, because at the only moment instructions can be written there is no upstream content yet. Dynamic data then has exactly one path downstream: a declared dep, which is V1-policed and hash-authenticated. (The pattern dap-bench's `seal-1` runtime uses at hop 1 — passing the planner's *output* as the collector's instruction — is precisely what this profile forbids; under `seal-vh-1` the plan must travel as a declared dep, `deps={1:[0]}`.)

**(b) every seal binds the delivered view — makes V1 post-hoc auditable, closing Limitation B absent collusion.** The seal payload gains

> `view_hash = sha256_b64u( canonical_json( {"goal": Lid.goal, "instruction": instruction_k, "inputs": [<declared tier bodies, in deps order>]} ) )`

computed over the W(k) actually delivered to hop *k* and signed with the **hop agent's** key — the agent attests to what it was shown. New verification rules:

| Rule | Check | Error |
|---|---|---|
| S0 | `Lid.profile` in the verifier allow-list; every seal `typ` matches it | `ERR_PROFILE_NOT_ALLOWED` / `ERR_PROFILE_MIXED` |
| S9 | seal *i*'s `view_hash` == hash of W(i) **reconstructed from the sealed Dabba alone** | `ERR_VIEW_HASH` |

S9 runs per seal after S2–S7, because reconstruction is only meaningful over an authenticated Lid core and hash-verified earlier tiers (every dep of hop *i* is `< i`, so its tier hash was already checked). Reconstruction is possible at all *only because of (a)*: W(i) is now a pure function of sealed data — goal, instructions, deps, and dep-tier bodies. A Station that delivers anything other than the declared view yields an attested hash no honest reconstruction matches. Scoped delivery thereby moves from "runtime property of a trusted Station" to a fact checkable from the artifact: the defensible claim for `seal-vh-1` upgrades from *enforces* to **"proves scoped delivery, absent Station–agent collusion."**

### 9.2 What `seal-vh-1` does NOT give (read before citing)

- **Collusion defeats S9.** A Station and a hop agent acting together can attest a false `view_hash` (hash the declared view, deliver a different one). The profile removes the need to trust the Station *alone*; it does not survive the custodian and the attestor conspiring.
- **External tool inputs are outside the attestation boundary.** `view_hash` covers W(k) — what the Station delivered. A hop that fetches external data itself (dap-bench's collector reading documents via its tool closure) attests nothing about those bytes. The collector-hijack finding (a poisoned document turning the collector, which then emits the payload in its own sealed tier) is therefore NOT prevented by this profile. What it adds is post-hoc **localization**: the sealed views prove the downstream hop's view was exactly the declared one, so a leaked payload provably entered through the compromised hop's sealed tier — the audit can name the hop, not just the outcome.
- **In-process v0 shares one trust domain.** With Station and agents in one process, agent-key attestation is organizationally the same signer. The property that matters now is that the sealed artifact alone carries the proof obligation — a later out-of-process deployment (agents holding their own keys) inherits S9 unchanged and only then gains its full independent force.
