# olinool REGISTRY — profiles, claims, errors, assurance (v0.3)

The authoritative registry the profile allow-list and closed error set point at.
Normative definitions live in `SPEC.md`; this file is the flat index. Adding a
profile, claim, error code, or assurance level is a deliberate, reviewed change —
the sets are closed (AINTIRAM MURAI: closed sets, no in-band negotiation).

## Profiles

A profile owns the per-encoding codec (R1 envelope + R2 signature + mint-side
serialize/canonicalize). Selection is by each profile's **predicate** over the
artifact's own markers, gated by `Policy.allowed_profiles` (default `{jws-1}`).
No peer negotiation; downgrade is structurally impossible (§SPEC 15).

| id | status | selection predicate (defined function) | envelope | canon | sig |
|---|---|---|---|---|---|
| `jws-1` | **active, frozen** | receipts/results: `header.typ ∈ {olinool-receipt+jws, olinool-result+jws} AND payload.v == "0.1"`; invocations: `header.typ == "olinool-invocation+jws"` (no version claim) | compact JWS, `alg:"EdDSA"` | RFC-8785 (JCS) | Ed25519 |
| `sd-1` | **active — Python + TypeScript (2026-07-07)** | SD-JWT `~`-combined structure + `header.typ ∈ {olinool-receipt+sd-jwt, olinool-invocation+sd-jwt, olinool-result+sd-jwt}` (+ `payload.v == "0.1"` for receipts/results); R5 preimage = issuer-signed base (RFC 9901) | SD-JWT combined form | RFC-8785 (JCS) | Ed25519 |
| `cose-mldsa-1` | reserved (not built) | COSE structural tag + `typ` | COSE | — | ML-DSA-65 (§SPEC 9b) |

Rules: exactly one profile per artifact; all hops in a chain + the invocation +
any result share one profile (`ERR_PROFILE_MIXED` otherwise). `jws-1` is frozen —
once released its bytes/verdicts never change; fixes ship as a new id. A breaking
change to any profile takes a NEW id (e.g. `jws-2`), never a mutation.

## Closed error set

Verification codes (conformance-assertable, exact strings):

| code | rule | meaning |
|---|---|---|
| `ERR_STRUCTURE` | R1 | malformed envelope / non-EdDSA `alg` / bad claim schema |
| `ERR_SIG` | R2 | receipt signature invalid for claimed issuer |
| `ERR_ROOT_UNTRUSTED` | R3 | root not self-issued, or principal not trusted by policy |
| `ERR_LINKAGE` | R4 | issuer/subject continuity or stable-principal break |
| `ERR_PARENT_HASH` | R5 | `prh` does not match the exact parent artifact bytes |
| `ERR_SCOPE_WIDENED` | R6 | child scope not ⊆ parent scope |
| `ERR_TIME_NOT_NESTED` | R7 | child validity window not nested in parent |
| `ERR_EXPIRED` | R7b | leaf outside its validity window vs wall clock |
| `ERR_DEPTH` | R8 | chain exceeds a hop's declared `max_depth` budget |
| `ERR_REVOKED_EPOCH` | R9 | hop epoch below the policy-required epoch |
| `ERR_ASSURANCE` | R10 | chain assurance level below policy floor |
| `ERR_AUDIENCE` | R11 | receiver not in leaf `aud`, or invocation `aud` mismatch |
| `ERR_POP` | R12 | possession failure (binding, freshness, signer, parse) |
| `ERR_REPLAY` | R12 | invocation nonce already seen |
| `ERR_RESULT_STRUCTURE` | §14 | result artifact malformed / bad schema |
| `ERR_RESULT_SIG` | §14 | result signature invalid for `sub` (`kid`==`sub`) |
| `ERR_RESULT_BINDING` | §14 | result not bound to the presented leaf receipt |
| `ERR_PROFILE_NOT_ALLOWED` | §15 | artifact's profile not in the allow-list (before claim logic) |
| `ERR_PROFILE_MIXED` | §15 | a chain/invocation/result mixes profiles |

Package-local (NOT part of olinool's closed set): `ERR_TOOL_NOT_GRANTED`
(olinool-mcp scope gate on one concrete tool call).

Corpus-assertability status: every code in the closed set is corpus-asserted
in BOTH verifiers. The one historical exception is retired: `ERR_PROFILE_MIXED`
(surfaced 2026-07-05 as inexpressible — a mixed verdict needs two artifacts
classifying as two different registered-and-allowed profiles IN BOTH verifiers,
and only jws-1 existed) became expressible on 2026-07-07 when `sd-1` landed in
the Python registry AND in `typescript/src/verify.ts` (registry-mirroring
`selectProfile` + SD-JWT decode), and is now asserted at the chain slot
(v14, mixed jws-1×sd-1 chain) and the invocation slot (v15, sd-1 chain
exercised by a jws-1 invocation). Known remaining hole, stated honestly: the
result-slot MIXED branch (`verify_result`'s result-vs-leaf profile match)
exists in both verifiers but is asserted by NO test or vector yet — a
data-only result-mix vector needs the sd-1 result mint, which has not shipped
(SPEC §16 status). The single-profile sd-1 vectors certify both verifiers as
of the same date: `sd01`/`sd02` at the chain slot (redacted-ALLOW,
disclosure-tamper→`ERR_STRUCTURE`) and `sd03`/`sd04` at the invocation slot
(2026-07-07) — `sd03` ALLOW (invocation rcp binds the leaf's issuer-signed
base, §16.4) and `sd04` `ERR_POP` (rcp binds the combined presented form: the
cross-language regression guard that closes the prior Python-only gap).
`ERR_PROFILE_NOT_ALLOWED` is corpus-asserted at all three slots — chain (v09
disallowed profile; v12 unknown profile version; v13 explicit empty
allow-list), invocation (v10), and result (v11, 2026-07-07) — in both the
Python and TS verifiers.

## Receipt claims (`jws-1`, payload)

`v` · `rid` · `prh` (null at root) · `pri` · `iss` · `sub` · `aud` (optional list) ·
`scope` · `cst` = {`iat`, `exp`, `max_depth`, `epoch`} · `asr` = {`level`, `evidence`}.
Invocation: `typ` · `rcp` · `sub` · `aud` · `req` · `iat` · `nnc`.
Result (§14): `v` · `typ` · `rid` · `rcp` · `inv` (nullable) · `sub` · `status` · `out` · `ver` · `iat`.

## Assurance levels (`asr.level`; chain level = min over hops)

| level | status | meaning |
|---|---|---|
| `0` | implemented | software signature only — authority proven, integrity asserted |
| `1` | reserved | RATS-aligned EAT evidence binds issuing runtime measurement to the receipt |
| `2` | research | chained attestation (predecessor keys measured into successor) |
