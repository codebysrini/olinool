# olinool — Delegation Receipts for Agent-to-Agent Calls
## Wire-format and verification specification, v0.1-draft

**Status:** working draft; matches the reference implementation in `python/` and the vectors in `python/olinool/conformance/vectors/` (shipped inside the wheel).
**Lineage:** successor to the PCD design (private design notes, outside this repo), with the holes found in the July 2026 teardown closed: chain-linkage rule, proof-of-possession, audience binding, defined scope algebra, closed error set.
**Prior art this spec deliberately positions against:** UCAN delegation/invocation, Biscuit, AIP (draft-prakash-aip-00). See §10 interop mapping.

**Naming system** (locked 2026-07-02, drawn from Mamuni Mayan's Aintiram / Vaastu tradition — see Mercay, *Fabric of the Universe*): **olinool** (ஒளி நூல், "thread of light" — the Tamil name of the Brahma Sutra, the luminous axis that carries order through a structure) names the library and the receipt chain. **muthirai** (முத்திரை, seal — Chola administrative lineage, not from the Aintiram corpus) names the mint/attenuate module: the seal pressed at each delegation. **ayadi** (from Ayadi Gananam — the verification mathematics applied before a structure may be trusted) names verification and the conformance suite. **vinkaru** (விண்கரு, "seed of space") names the root receipt / trust anchor. **moolam** (மூலம், the primal dot — the source) names the shared root-layer package all packages depend on.  Names attach to modules and concepts; public API identifiers stay descriptive English so contributors need no Tamil to use the library.

---

## 1. Model

A **principal** (human/org authority) delegates to an agent; agents re-delegate down a chain. Each delegation emits one **Receipt** — a compact JWS signed by the delegating party. Exercising authority against a **receiver** requires the full Receipt chain plus one **Invocation** — a short-lived JWS by the leaf subject binding the chain to one concrete request and one receiver.

Verification is entirely offline: keys are resolved through a pluggable resolver (A2A Agent Card / `.well-known` in production), the clock and revocation-epoch lookup are injected. There is no gateway and no central log. The chain *is* the authority trail.

Two invariants, receiver-enforced:

1. **Monotonic attenuation** — every hop's scope ⊆ parent scope, time window nested, depth budget decreasing (§5 R6–R8).
2. **Possession** — only the leaf subject's key can use the chain, only at the named receiver, only for the hashed request, once (§6 R11–R12).

## 2. Identity and key discovery

Agent ids are opaque strings (recommendation: `did:web:` form). Verifiers resolve id → Ed25519 key via a **KeyResolver**. Production profile: A2A Agent Card carries the key + declared `min_assurance` per scope; resolution is HTTPS `.well-known`, cache TTL ≤ 5 min.

Honesty note: resolving keys via `.well-known` makes WebPKI + DNS the de-facto trust root. This spec does not claim "no CA"; it claims *no additional* CA.

## 3. Receipt format

Compact JWS: `b64u(header) . b64u(payload) . b64u(Ed25519 sig)`.
Header: `{"alg":"EdDSA","typ":"olinool-receipt+jws","kid":"<issuer id>"}`.
Canonicalization: RFC 8785 (JCS) over both header and payload before encoding.

| Claim | Type | Meaning |
|---|---|---|
| `v` | `"0.1"` | version |
| `rid` | uuid string | receipt id |
| `prh` | b64u sha256 \| null | hash of parent Receipt JWS bytes; null only at root |
| `pri` | id | root principal; constant down the chain |
| `iss` | id | delegating party; MUST equal parent `sub` (root: MUST equal `pri`) |
| `sub` | id | delegate; the only key that may invoke on this hop |
| `aud` | [pattern] (opt) | receivers this hop may be presented to (fnmatch patterns) |
| `scope` | Scope (§8) | granted authority; MUST be ⊆ parent scope |
| `cst` | object | `iat`,`exp` (s), `max_depth` (int, remaining delegations), `epoch` (int) |
| `asr` | object | `level` 0\|1\|2, `evidence` (null at L0; reserved: EAT at L1/L2, §9) |

## 4. Invocation format

Header `{"alg":"EdDSA","typ":"olinool-invocation+jws","kid":"<leaf sub>"}`. Payload: `typ:"olinool-invocation"`, `rcp` = sha256(leaf Receipt JWS), `sub` = leaf subject, `aud` = receiver id (exact), `req` = sha256(request bytes), `iat`, `nnc` nonce.

The request-byte hashing rule per transport binding (§11) must be normative for interop; v0.1 hashes the exact payload bytes handed to the receiver.

## 5. Chain verification (normative order, closed errors)

A verifier MUST evaluate R1–R10 and return the FIRST failure:

| Rule | Check | Error |
|---|---|---|
| R1 | each JWS parses; header alg/typ; claims schema; version; chain length ≤ policy max | `ERR_STRUCTURE` |
| R2 | each hop signature valid for `iss` key; `kid` == `iss` | `ERR_SIG` |
| R3 | root: `prh` null, `iss`==`pri`, `pri` ∈ policy trust set (if set) | `ERR_ROOT_UNTRUSTED` |
| R4 | ∀i>0: `iss_i` == `sub_{i-1}` and `pri_i` == `pri_0` | `ERR_LINKAGE` |
| R5 | ∀i>0: `prh_i` == sha256(exact parent JWS bytes) | `ERR_PARENT_HASH` |
| R6 | ∀i>0: `scope_i` ⊆ `scope_{i-1}` per §8 | `ERR_SCOPE_WIDENED` |
| R7 | windows nest (`iat` non-decreasing, `exp` non-increasing); leaf window contains now ± skew | `ERR_TIME_NOT_NESTED` / `ERR_EXPIRED` |
| R8 | ∀i: remaining hops after i ≤ `max_depth_i` (ancestor budgets cap forged inflation) | `ERR_DEPTH` |
| R9 | if policy exposes `current_epoch(iss)`: hop epoch ≥ it | `ERR_REVOKED_EPOCH` |
| R10 | min hop `asr.level` ≥ policy `min_assurance` | `ERR_ASSURANCE` |

R4 + R5 together are what make the chain a chain: R4 stops "anyone mints a child of a public receipt", R5 stops splicing a hop onto a different-but-plausible parent. The original PCD sketch specified neither; without them the design is trivially forgeable.

## 6. Invocation verification

| Rule | Check | Error |
|---|---|---|
| R11 | leaf `aud` (if present) matches receiver; invocation `aud` == receiver | `ERR_AUDIENCE` |
| R12 | invocation signed by leaf `sub`; `rcp` == hash(presented leaf); `req` == hash(request); fresh (`iat` within ttl+skew); nonce unseen | `ERR_POP` / `ERR_REPLAY` |

R12 is what turns bearer receipts into held credentials: a stolen or truncated chain is unusable without the leaf subject's private key. Replay caching is per-receiver, in-memory in the reference; multi-instance receivers need a shared cache — a deployment concern, stated, not hidden.

## 7. Error codes

Closed set, conformance-assertable: `ERR_STRUCTURE, ERR_SIG, ERR_ROOT_UNTRUSTED, ERR_LINKAGE, ERR_PARENT_HASH, ERR_SCOPE_WIDENED, ERR_TIME_NOT_NESTED, ERR_EXPIRED, ERR_DEPTH, ERR_REVOKED_EPOCH, ERR_ASSURANCE, ERR_AUDIENCE, ERR_POP, ERR_REPLAY`. v0.2 adds the result-record codes (§14): `ERR_RESULT_STRUCTURE, ERR_RESULT_SIG, ERR_RESULT_BINDING`. v0.3 adds the profile-selection codes (§15): `ERR_PROFILE_NOT_ALLOWED, ERR_PROFILE_MIXED`.

## 8. Scope algebra (v0)

Interop dies if two implementations disagree on ⊆, so v0 is deliberately small and total:

```
Scope  := [Grant+]
Grant  := {act: token | "*", res: pattern, limits?: {key: number}}
pattern: literal, optionally ONE trailing "*"
```

`child ⊆ parent` iff every child grant is covered by ≥1 parent grant:
`act` — parent `*` covers all; else exact match; child `*` needs parent `*`.
`res` — trailing-star prefix subsumption (`db/*` covers `db/eu`, `db/eu/*`); literal covers only itself.
`limits` — every parent limit key must appear in the child with value ≤ parent's (a child that *drops* a ceiling is unbounded ⇒ widened — corpus v02/c04). Children may add keys.

Excluded from v0 on purpose: regex/mid-string globs (subsumption undecidable-ish, disagreement magnet), Datalog policies (Biscuit/AIP already own that; we interop instead), negative grants. Numeric `limits` are **per-action ceilings**, not cumulative budgets — cumulative enforcement needs shared state and is explicitly out of the artifact (same stance AIP takes).

## 9. Assurance ladder

`asr.level` is the chain's integrity dimension; chain level = min over hops.

L0 (this spec, implemented): software signature only. Authorization is proven; integrity is asserted. ~0.05 ms/hop verify.
L1 (reserved): `evidence` carries a RATS-aligned EAT bundle binding the issuing runtime's measurement to the Receipt (`rid` as nonce). Align with draft-huang-rats-agentic-eat-cap-attest rather than inventing an evidence format.
L2 (research): chained attestation (predecessor verifier keys measured into successor). Attestation transitivity has no native TEE support in 2026; L2 stays a research track, not a roadmap promise.

Receivers publish per-scope `min_assurance` in their Agent Card; verifiers enforce via R10.

### 9b. Cryptographic profile and PQC posture

v0.1 mandates Ed25519 exclusively — no algorithm negotiation, none accepted (R1 rejects any other `alg`; conformance test c20 covers the downgrade/`alg`-swap attack class). Rationale, carried from the PoC decision record: receipts are short-lived *signature* artifacts, so harvest-now-decrypt-later does not threaten them — a quantum forgery of an already-expired receipt is worthless. Post-quantum migration therefore targets, in order: (1) **long-lived identity keys** (agent/principal keys live months–years; a CRQC could mint fresh receipts from broken identity keys) — ML-DSA-65 via a versioned profile (`olinool/2`), single-alg again, as a version bump not a negotiation; (2) **archived chains kept as evidence** — protected by periodic hash anchoring (SHA-256 remains adequate under Grover), not by re-signing. Cost note for the migration: ML-DSA-65 signatures are ~3.3 KB vs Ed25519's 64 bytes — a 5-hop chain grows from a few KB to ~20 KB, so token-by-reference becomes mandatory at that point. Hot-path receipts stay classical until identity/anchoring layers exist; putting ML-DSA on per-hop receipts today is size cost with no matching threat.

## 10. Interop mapping (the bridge that keeps us honest)

| Concept | olinool | AIP (draft-prakash-aip-00) | UCAN | Biscuit |
|---|---|---|---|---|
| Delegation unit | Receipt (per hop, JWS) | Biscuit block in one token | Delegation (per hop, DAG-CBOR) | Block |
| Chain link | `prh` hash + iss==parent.sub | block order in token | `prf` CID + aud==iss | block chaining |
| Use binding | Invocation JWS (PoP) | invocation-bound claims | Invocation + Receipt | sealed token / PoP |
| Attenuation check | receiver, R6 algebra | receiver, Datalog | receiver, capability semantics | Datalog |
| Runtime attestation slot | `asr` + EAT (L1+) | — | — | — |
| Outcome record | `olinool-result` (§14) | Completion block | Receipt (attested result) | — |

Bridge plan (v0.2): `olinool.bridge.aip` — verify an AIP chained token and emit the equivalent Receipt chain view, so an olinool receiver can accept AIP callers. The differentiators we keep: per-hop portability/archival, the attestation slot, and the conformance corpus.

## 11. Transport bindings

A2A: chain + invocation ride `metadata.olinool` on task submission; Agent Card advertises key + `min_assurance`. HTTP: `Authorization: Olinool <b64u(chain)>` + `X-Olinool-Invocation`. DAP: Receipt hash pinned in the Dabba Lid; DAP is an *adapter, not a dependency* — the library must adopt without DAP existing. Two DAP concepts survive inside olinool regardless of whether DAP ships as a transport: the append-only Tiers + seal chain are the design source for `olinool-result` outcome records (v0.2), and scoped working views W(v) are the honest basis of the "fast" claim — each agent receives only its slice of context, which cuts tokens, latency, cost, and prompt-injection surface; that claim graduates from DESIGN to TESTED only via benchmark, in DAP's own track.

## 12. Known gaps (deliberate, v0.1)

1. **Cumulative budgets** need a central counter; the artifact carries ceilings only.
2. **Revocation** = TTL + epoch + optional feed; instant universal revocation is not offered offline. Regulated deployments needing it must run the central-mint profile.
3. **Chain privacy — narrowed by `sd-1` (§16), not closed**: under `jws-1` the full chain disclosed upstream org/agent/scope structure to every receiver. `sd-1` (implemented 2026-07-07 in both verifiers — Python mint+verify, TS verify) narrows this: the non-linkage claims (`rid`, `asr.evidence`, `ext.*` display metadata) ride salted-hash disclosures the holder may withhold per presentation (withholding a claim the data model requires fails closed — §16.2, so `rid` still reaches full-verifying receivers), and a third-party auditor can confirm linkage while learning nothing else. What stays open, deliberately: the linkage set (`iss`/`sub`/`scope`/`prh`/`cst` window, plus `aud` per the §16.3 design note) remains visible to every full-verifying receiver, because R4/R6 must read `sub`/`scope` to re-verify continuity and monotonic attenuation. Full upstream scope-privacy is therefore still a gap: blinding a receiver to `scope` would downgrade R6 from re-verified to asserted — a weakening this spec refuses; zero-knowledge subset proofs are a research track, out of `sd-1`'s scope (§16.5).
4. ~~No outcome records yet~~ **Closed in v0.2**: `olinool-result` records (§14) carry the action half. `ver` levels above `self` (counter-signature, attestation) remain format slots only — self-reported results are still the honest baseline.
5. ~~JCS approximation in the prototype~~ **Closed in v0.2**: moolam canonicalizes via strict RFC 8785 (`rfc8785` package), with known-answer vectors and a v0.1 byte-parity guard proving no wire break for previously minted artifacts.

## 13. Conformance

The corpus vectors (`python/olinool/conformance/vectors/*.json`, shipped in the wheel; self-certify any install with `python -m olinool.conformance`) are self-contained (keys inline). An implementation conforms iff it reproduces `expect.allowed`/`expect.error` exactly on all vectors. Reference: the Python pytest suite (superset), 22 exported vectors (`v01`–`v08` chains/invocations, `v09`–`v13` profile-selection cases, `v14`–`v15` mixed-profile cases, `sd01`–`sd02` sd-1 selective-disclosure chain cases, `sd03`–`sd04` sd-1 invocation-binding cases, `r01`–`r03` result records), `conformance/run.py` runner; the same corpus certifies the TypeScript verifier (`typescript/test/corpus.test.ts`) — both verifiers must produce identical verdicts on every vector, and do as of 2026-07-07 (the transitional sd01–sd02 Python-only exception is retired). The corpus is format-first: AIP/UCAN bridge vectors get added under the same harness so the suite can certify *any* agent-delegation verifier — that neutrality is the point.

## 14. Result records (v0.2)

A Receipt chain proves *authority*; a **Result record** is the leaf subject's signed statement of the *action taken* under it — the artifact §12.4 required before any self-auditing claim. Mirrors UCAN receipts / AIP Completion blocks (§10).

Compact JWS. Header `{"alg":"EdDSA","typ":"olinool-result+jws","kid":"<acting agent id>"}`.

| Claim | Type | Meaning |
|---|---|---|
| `v` | `"0.1"` | version |
| `rid` | uuid string | result id |
| `rcp` | b64u sha256 | hash of the leaf Receipt JWS this attests to (authority link) |
| `inv` | b64u sha256 \| null | hash of the Invocation JWS (exact-request link, optional) |
| `sub` | id | acting agent; MUST equal leaf Receipt `sub`; is the signer (`kid`==`sub`) |
| `status` | enum | `completed` \| `failed` \| `partial` |
| `out` | b64u sha256 | hash of the output bytes |
| `ver` | enum | verification level: `self` (default) \| `counter` \| `attested` — levels above `self` are reserved format slots |
| `iat` | int (s) | mint time |

Verification (normative order, first failure wins): structure/enums/schema → `ERR_RESULT_STRUCTURE`; signature valid for `sub` with `kid`==`sub` → `ERR_RESULT_SIG`; binding — `sub` == leaf `sub` and `rcp` == sha256(presented leaf JWS bytes) → `ERR_RESULT_BINDING`.

Results are archival artifacts, not credentials: no freshness window, no replay cache, no audience. A result does not prove the output is *correct* — `ver:"self"` is self-reported by construction; counter-signing receivers and attested runtimes are the reserved upgrade path. Corpus vectors: `r01`–`r03`. The dabba bridge emits this format for sealed tiers (output bytes = tier body), cross-linking the action chain to the authority chain.

## 15. Profiles: the data-model / encoding split (v0.3)

The verification model separates two layers (design `DESIGN_profile_split_v0.3.md`, implemented v0.3): a **profile** owns the per-encoding codec (R1 envelope parse + R2 signature + mint-side serialize/canonicalize); the **data model** (R3–R12 claim logic, scope algebra, closed errors) is encoding-agnostic and operates only on decoded claim dicts plus the profile-provided `artifact_bytes` — the R5 parent-hash preimage, defined per profile: for `jws-1` the verbatim wire string, for `sd-1` the issuer-signed base (§16.4). The verifier never re-serializes to compute a parent hash.

**`jws-1`** is the v0.1 wire format, now named: compact JWS, `alg:"EdDSA"`, `typ` ∈ {`olinool-receipt+jws`, `olinool-invocation+jws`, `olinool-result+jws`}, receipt/result payload `v:"0.1"`, RFC-8785 canonicalization, Ed25519. **The split changes zero bytes on the wire**: v0.1 artifacts ARE `jws-1` by definition of their existing markers — no new field, no re-signing. `jws-1` is frozen: once released its bytes and verdicts never change; fixes ship as a NEW profile id, never a mutation.

**Selection predicate** (per profile, recorded in `REGISTRY.md`): `jws-1` selects on `(typ, v)` for receipts and results, and on `typ` alone for invocations (which carry no version claim). Selection reads the artifact's **own markers** — never a peer's advertisement (instinct 9; the c20 no-downgrade doctrine generalized from algorithms to whole encodings).

**Allow-list model.** A `Policy` carries `allowed_profiles` (default `{"jws-1"}`). An artifact whose profile is not allowed — or matches no profile — is rejected with `ERR_PROFILE_NOT_ALLOWED` **before any claim logic**. Downgrade is structurally impossible: nothing a peer sends can widen what a verifier accepts.

**Uniform-profile rule (v0.3).** All receipts in a chain MUST share one profile, and the invocation (and any result) MUST match the chain's profile; otherwise `ERR_PROFILE_MIXED`. Cross-profile chains are a deliberate future question, pinned closed now for auditability.

Profile evolution stays out of band: an additional profile — SD-JWT (`sd-1`, §16; shipped 2026-07-07 in both verifiers) or the future PQC (`cose-mldsa-1`, §9b) — is a NEW id with its own frozen definition, coexisting with `jws-1`; the transport chooses which envelope it can carry, never what a receipt *is*.

## 16. `sd-1` — selective-disclosure profile (SD-JWT, RFC 9901)

**Status: IMPLEMENTED — Python reference + TypeScript verifier (2026-07-07).** The Python codec (`python/olinool/profiles/sd1.py`) certifies against corpus vectors `sd01`–`sd04` and the `tests/test_sd1.py` suite; mint support is the `profile="sd-1"` option on `mint_root`/`attenuate` (default unchanged: `jws-1`, golden-bytes-proven). The TS verifier (`typescript/src/verify.ts`) carries a registry-mirroring `selectProfile` (envelope family + marker predicate), the SD-JWT combined-form decode with digest-checked disclosure resolution, and the same R5/`rcp` base-preimage seam; the cross-verifier certification `REGISTRY.md` requires is CLOSED — both verifiers produce identical verdicts on all 22 corpus vectors, which unblocked the mixed-profile vectors v14/v15 (§13). Minting in TS remains out of scope (verify-only port). `sd-1` invocation/result MINT paths are not yet exposed in Python either (`invoke`/`mint_result` still press jws-1); the verifier accepts sd-1 invocations per §16.1, now corpus-asserted CROSS-LANGUAGE by `sd03` (invocation ALLOW, rcp binds the issuer-signed base) and `sd04` (the combined-form-preimage regression → `ERR_POP`), closing the prior Python-only gap. `verify_result` remains jws-1-practical until the result mint ships. The R5 preimage seam (§16.4) is implemented in both verifiers (byte- and verdict-neutral for `jws-1`).

Motivation: §12.3 — today every receiver sees the full upstream chain in cleartext. `sd-1` lets the holder hide claims that no verification rule reads, and lets a third-party auditor confirm linkage without seeing anything else. It changes the ENCODING/disclosure layer only: Ed25519 stays (§9b single-algorithm policy — PQC is `cose-mldsa-1`, a different seam), and the R1–R12 data model, claim semantics, and closed error set (§7) are untouched.

### 16.1 Envelope (combined form)

An `sd-1` artifact is an SD-JWT in combined form (RFC 9901):

```
<issuer-signed JWT>~<Disclosure 1>~...~<Disclosure N>~
```

- The **issuer-signed JWT** is compact JWS: `alg:"EdDSA"`, header `typ` ∈ {`olinool-receipt+sd-jwt`, `olinool-invocation+sd-jwt`, `olinool-result+sd-jwt`}, `kid` as in §3. Its payload carries the mandatory-disclosed claims in cleartext (§16.3) plus `_sd` (the disclosure-digest array) and `_sd_alg:"sha-256"` — **pinned**; any other `_sd_alg` value is `ERR_STRUCTURE` (instinct 9: no in-band hash negotiation).
- **No KB-JWT.** Possession is olinool's own Invocation (R12), not SD-JWT key binding; the combined form always ends with `~`.
- **Selection predicate** (§15 doctrine — the artifact's own markers): `~`-delimited combined structure AND `typ` as above AND payload `v == "0.1"` for receipts/results (`typ` alone for invocations, which carry no version claim).
- Invocations and results under `sd-1` define no disclosable claims in this version — their combined form is `<JWT>~` — and exist so the §15 uniform-profile rule can hold across a full `sd-1` verification.

### 16.2 Salted-hash disclosure format

Per RFC 9901: `Disclosure = b64u(JSON [salt, claim_name, claim_value])` with a ≥128-bit cryptographically random salt, unique per disclosure; `digest = b64u(sha256(ascii(Disclosure)))`, listed in the payload's `_sd` array. The object-valued claim case (`asr.evidence` inside `asr`) uses RFC 9901 structured-claim (nested) disclosures. Decode resolves the presented disclosures into the claim dict BEFORE the R1b schema check: an unknown digest, duplicate digest, or malformed disclosure → `ERR_STRUCTURE`; a withheld disclosure whose claim the data model requires fails closed at R1b (`ERR_STRUCTURE`). No new error codes — §7's closed set is unchanged.

### 16.3 Claim split — what may hide, what must not

Two sets, fixed by which claims the verification rules read:

**Mandatory-disclosed linkage set** (cleartext in the issuer-signed base; can never be withheld): `iss`, `sub` (R2/R4), `scope` (R6), `prh` (R5), the `cst` window `iat`/`exp` (R7). Structural completion by the same criterion: `v` (selection predicate), `pri` (R3/R4), `cst.max_depth` (R8), `cst.epoch` (R9), `asr.level` (R10). These are exactly the claims some rule must read on every hop; hiding any of them would downgrade that rule from re-verified to asserted.

**Disclosable set** (salted-hash disclosures; holder-selectable per presentation): `rid` (correlation handle — no chain rule reads it, but R1b's schema requires it, so full verification still needs its disclosure); `asr.evidence` (R10 reads only `level`; L1+ evidence bundles are precisely the payloads a third party shouldn't see); and principal display identity metadata (`ext.*` display claims — the `pri` linkage identifier itself is read by R3/R4 and stays cleartext).

Design note (implementation resolution, 2026-07-07 — third internal contradiction, same family as the two below): an earlier draft of this section listed *upstream `aud`* as disclosable ("only the leaf's `aud` is read, R11 — the leaf must disclose it to the receiver"). Refused at implementation: §16.3's own criterion — every claim a verification rule reads is mandatory — covers `aud`, because R11 reads the leaf's `aud` *conditionally* ("if present") and leaf-ness is positional (any receipt may be presented as a leaf). A withheld `aud` disclosure is indistinguishable from an absent `aud`, so a holder could make an audience-restricted receipt look unrestricted — a WIDENING channel ("must disclose" was holder-cooperative, not verifier-enforced). Hidden must never equal absent; `aud` is therefore mandatory-cleartext on every hop. Every claim that remains disclosable fails CLOSED when withheld (`rid` → R1b `ERR_STRUCTURE`) or is read by no rule (`asr.evidence`, `ext.*`). Residual leak, stated honestly: upstream audience restrictions stay visible to receivers, like the rest of the linkage set.

Design note (resolves the July 2026 sketch): the sketch floated hiding *exact `cst` timestamps* behind disclosures. Refused here: R7 window nesting is monotonic attenuation in time (the clock is a security mechanism), and an auditor confirming "narrowed properly" must re-verify it exactly like R6. Consequence, stated honestly: issuance/expiry bounds remain visible to every party — a residual timing-metadata leak.

### 16.4 R5 preimage rule (the one data-model seam — implemented)

Under `sd-1`, `prh_i` = sha256 over the parent's **issuer-signed base** — the compact JWT before the first `~` — never over the combined form. The combined form varies with which disclosures the holder later presents; a child must bind a stable parent identity fixed at mint time, independent of downstream holder choices.

Generalized data-model statement (implemented in both verifiers): R5's preimage is the profile-provided `artifact_bytes` from the profile's decode — for `jws-1` the verbatim wire string (byte-identical to pre-refactor behavior, proven by the golden-bytes oracle and the frozen corpus), for `sd-1` the issuer-signed base. The verifier never re-serializes to compute a parent hash. The same preimage rule is implemented for the Invocation leaf-binding hash (`rcp`, §4/R12) in both verifiers and is now corpus-asserted CROSS-LANGUAGE by `sd03` (ALLOW: rcp binds the issuer-signed base, stable across a withheld disclosure) and `sd04` (`ERR_POP`: rcp binds the combined presented form instead — the regression guard against a verifier hashing the presentation rather than the base), in addition to `tests/test_sd1.py` in Python; the Result `rcp` (§14) follows when the sd-1 result mint ships — `verify_result` is jws-1-practical today.

### 16.5 The privacy claim — narrowed, not eliminated

`sd-1` NARROWS §12.3's chain-privacy gap; it does not close it. Precisely:

- **To a full-verifying receiver (R1–R12):** upstream `sub`/`scope` — the org/agent/scope structure — remain visible, because R4/R6 must read them (and `aud` stays visible per the §16.3 design note). What newly hides: `asr.evidence`, display metadata, and — from any party the holder chooses not to correlate across — `rid`. Blinding a receiver to `scope` would silently downgrade R6 from re-verified to asserted — a weakening this spec refuses; a zero-knowledge subset proof is a research track, out of `sd-1`'s scope.
- **To a third-party auditor (linkage confirmation only):** the holder may withhold every disclosure; the auditor still verifies signatures, issuer/subject continuity, parent hashes, and scope/window attenuation over the mandatory set, and learns nothing else. This is `sd-1`'s honest payoff: cross-org confidentiality of non-linkage claims plus selective disclosure to auditors. (Auditor mode is a presentation/consumption pattern over the same artifacts; this spec adds no new verifier entry point for it.)

Claims discipline: any public statement about `sd-1` must say it *narrows* the chain-privacy gap — never that the chain is hidden from receivers. Full upstream scope-privacy stays a documented gap (§12.3).
