# v0.3 keystone — data-model / profile split

**Status: IMPLEMENTED on branch `v0.3-profile-split` (2026-07-05).** The seam ships as `olinool/python/olinool/profiles/` (`jws-1` as its first occupant); the §1 guarantee is proven by the golden-bytes oracle (`tests/test_golden_bytes.py`, byte-identical mint across the refactor) and the frozen corpora (11/11 + 8/8 verdict-identical). Profile behavior is covered by `tests/test_profiles.py`; the model is recorded in `SPEC.md §15` and `REGISTRY.md`. Every other v0.3 item (SD-JWT, PQC, Go/TS parity) builds on this boundary. SPEC-before-implementation (AINTIRAM). Grounded in the `ayadi.py` R1–R10 structure (verified 2026-07-05).

_Implementation note (surfaced, not a redesign): unknown/disallowed-profile inputs previously rejected as `ERR_STRUCTURE` (wrong `v`, unknown `typ`) or `ERR_POP` (unknown invocation `typ`) now route to `ERR_PROFILE_NOT_ALLOWED`, per §5 "before any claim logic." These are already-invalid inputs; no frozen vector or existing test covered them, and no valid artifact's bytes or verdict changed. The alg-confusion case (c20) stays `ERR_STRUCTURE` — `alg` is an envelope check inside the codec, not a profile predicate._

## 1. The compatibility guarantee (the load-bearing promise — read first)

**The split changes zero bytes on the wire. v0.1 artifacts ARE profile `jws-1` by definition of their existing markers.** No new claim, no new header field, no re-signing. The frozen corpus (`olinool/corpus/*.json`, `dabba/corpus/*.json`) stays byte-identical AND verdict-identical after the refactor. This is a pure internal reorganization plus a spec formalization — not a wire change, not a `v` bump.

Enforced as a testable invariant (§8): the existing 8+8 conformance vectors must pass unchanged, and a golden-bytes test asserts `jws-1` minting reproduces current `muthirai` minting exactly.

If any step would alter a frozen artifact's bytes or verdict, it is a wire break → STOP and surface. The split is defined precisely so this cannot happen.

## 2. The boundary (what is a profile, what is the data model)

Two layers, cleanly separable because the current code already separates them:

- **Profile codec (per-encoding):** owns R1 (parse + structural schema) and R2 (signature envelope). Turns artifact bytes into `(claims: dict, sig_ok_for_key: fn, canonical_bytes: bytes)`. This is the JOSE/JWS specifics: compact-JWS parsing, `alg==EdDSA`, `typ`, Ed25519 verify, RFC-8785 canonicalization. A different profile (SD-JWT, COSE) replaces exactly this layer.
- **Data model (encoding-agnostic):** owns R3–R10 — root anchoring, issuer/principal linkage, parent-hash binding, monotonic scope attenuation, nested time windows, depth, epoch, assurance — plus the scope algebra, invocation possession (R11–R12), and the closed error set. Operates only on decoded claim dicts + the profile-provided canonical bytes (R5 hashes those). It never parses or verifies signatures itself.

The current `verify_chain` interleaves them in one function; the split extracts the R1/R2 block into a profile object and leaves R3–R10 as `verify_chain_claims(decoded, canonical_bytes, resolver, policy)`.

## 3. The Profile interface (concrete)

```python
class Profile(Protocol):
    id: str                       # "jws-1"  — stable, appears in REGISTRY.md and policy allow-lists
    receipt_typ: str              # marker used for selection (§5)
    invocation_typ: str

    def decode(self, artifact: str) -> Decoded:
        # R1: parse + structural schema. Raises ProfileParseError (-> ERR_STRUCTURE).
        # returns Decoded(header, claims, signing_input, sig, canonical_bytes)

    def verify_sig(self, decoded: Decoded, public_key) -> bool:
        # R2: envelope signature over signing_input.

    # mint side (muthirai):
    def serialize(self, header: dict, claims: dict, signer) -> str
    def canonicalize(self, obj: dict) -> bytes      # for hashing/signing
```

`jws-1` is the reference implementation of this interface and equals today's behavior exactly. `moolam` (crypto) stays underneath both — Ed25519/JCS live there; the profile composes them.

## 4. `jws-1` definition (frozen with this release)

`jws-1` ≡ the v0.1 format, now named: compact JWS, `alg:"EdDSA"`, `typ:"olinool-receipt+jws"` / `"olinool-invocation+jws"`, payload `v:"0.1"`, RFC-8785 canonicalization, Ed25519. It is frozen: once released, `jws-1`'s bytes and verdicts never change; fixes ship as `jws-2` (new profile id), never as a mutation. This mirrors the frozen-corpus law at the profile layer.

## 5. Profile selection + instinct-9 (no in-band negotiation)

- **Selection is by the artifact's own markers via a DEFINED PREDICATE, not by peer negotiation.** Each profile registers a selection predicate — for `jws-1` it is `(header.typ == "olinool-receipt+jws" AND payload.v == "0.1")`, i.e. **`(typ, v)` together, not `typ` alone** (ratified 2026-07-05): a future `jws-2` on the same JWS envelope needs `v` to disambiguate. "Self-identifying" is thus a defined function, not a vibe. REGISTRY.md records the predicate for every profile; profile selection = the first registered predicate that matches, else `ERR_PROFILE_NOT_ALLOWED`. A future SD-JWT profile predicate keys on its `~`-delimited structure + its own `typ`.
- **Policy carries an allow-list**, default `{"jws-1"}`. `Policy.allowed_profiles`. An artifact whose selected profile is not in the allow-list is rejected with `ERR_PROFILE_NOT_ALLOWED` (new closed-set code) before any claim logic. c20 doctrine generalized from algorithms to profiles: **one profile per artifact, acceptance by policy, downgrade structurally impossible.**
- **Uniform profile across the ENTIRE verification, not just chain hops** (ratified 2026-07-05): all chain receipts share one profile (`ERR_PROFILE_MIXED` otherwise), AND the invocation (R11–R12) and any result artifact MUST match the chain's profile (or, conservatively, be pinned `jws-1`). §5's original wording named only chain hops; invocation and result are independent artifacts and must be constrained too, else a mixed-profile attack re-enters through the possession/action artifacts. Reject-mixed is fail-closed and strictly reversible (allowing mixed later is a superset of accepted inputs — forecloses nothing).

## 6. Corpus reorganization

- Move the frozen vectors to `olinool/corpus/jws-1/` (they are jws-1). A compatibility shim or a one-line loader change keeps `conformance/run.py` finding them; the vector *bytes* do not change.
- New profiles get `olinool/corpus/<profile>/`. The runner iterates profiles.
- The corpus schema gains an optional `"profile"` field (defaults to `jws-1` when absent — preserving the existing vector files unchanged; absence = jws-1, same principle as §1).

## 7. Code refactor plan (mechanical, verdict-preserving)

- New `olinool/python/olinool/profiles/__init__.py` (registry: id → Profile) and `profiles/jws1.py` (the codec extracted from `muthirai._jws_sign` + `ayadi`'s R1/R2 block + `moolam` calls).
- `ayadi.verify_chain` → thin: select+decode+verify_sig per hop via the profile, then call the extracted `verify_chain_claims(...)` (R3–R10 verbatim, moved not rewritten).
- `muthirai.mint_root/attenuate` → build claims (unchanged), then `profile.serialize(...)` instead of the hardcoded `_jws_sign`. Default profile `jws-1`, so signatures/bytes are identical.
- `Policy` gains `allowed_profiles: set[str] = {"jws-1"}`.
- `errors.py` gains `ERR_PROFILE_NOT_ALLOWED`, `ERR_PROFILE_MIXED` (closed set stays closed).
- `invocation.py` / `result.py` get the same treatment (profile-parameterized, default jws-1).

Every move is copy-not-rewrite for R3–R12; the diff should contain no changed rule logic, only relocation + a dispatch seam.

## 8. Validation (the invariant that proves §1)

1. **Corpus unchanged:** `conformance/run.py` → 8/8 (olinool) + 8/8 (dabba), verdicts identical. Non-negotiable gate.
2. **Golden-bytes parity:** a test mints a fixed receipt under the refactored `jws-1` path and asserts the bytes equal a pre-refactor golden capture (deterministic given fixed keys/seed/time). Proves minting is byte-identical, not just verdict-identical.
3. **Full matrix green:** moolam / olinool / olinool-mcp / dabba unchanged counts.
4. **Negative profile test:** an artifact tagged with an unknown profile → `ERR_PROFILE_NOT_ALLOWED`; a chain mixing profiles → `ERR_PROFILE_MIXED`.

## 9. What this unblocks — and what is explicitly NOT in this step

Unblocks (future, each its own task): `sd-1` (SD-JWT selective-disclosure privacy profile, RFC 9901 — the cross-org disclosure fix), `cose-mldsa-1` (PQC, SPEC §9b), and clean Go/TS parity (they implement the same profile interface + data model). Also folds in two small v0.3 hardening items that touch the same files:
- **`REGISTRY.md`** — profile ids + their selection predicates (§5), claim names, error codes, assurance levels. Zero risk (doc). The profile allow-list points at it.
- **JSON double-safe number rule** (limits ∈ IEEE-754-exact) — NOT risk-free: it is a *validation-rule change* that could flip a verdict. It rides along ONLY after passing the §8.1 gate (no frozen verdict change). **Verified 2026-07-05:** frozen corpus limit values are `{5,10,25,50,500}`, all IEEE-754-exact → the rule is purely additive over out-of-spec values that never appear in the corpus → gate clears. Ships as its own commit in-branch; re-run the gate at implementation time to confirm nothing drifted.

NOT in this step: no SD-JWT implementation, no Go, no new crypto. This task delivers the *seam* + `jws-1` as its first occupant + the registry/number-rule hardening. SD-JWT and Go are the payoff that the seam makes possible, sequenced after it lands green.

## 10. Decisions (ratified by Srini 2026-07-05)

1. **Profile id: IMPLICIT** — jws-1 inferred from `(typ, v)` predicate (§5), zero wire change. An explicit `prof` claim would change payload bytes = the §1 wire break. Never retrofitted. New profiles self-identify via their registered predicate.
2. **Mixed-profile chains: REJECT** in v0.3 — fail-closed, strictly reversible. Extended (§5) to invocation + result artifacts, not just chain hops.
3. **Fold number-rule + REGISTRY.md into the branch: YES**, separate commits. REGISTRY.md zero-risk; number rule gated on §8.1 (verified clears — §9). No constitutional conflict; instinct-9 handling ratified.
