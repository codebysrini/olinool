# olinool as an MCP Extension — design draft v0.1 — private prototype (mcp-ext branch)

**Status:** PRIVATE PROTOTYPE. §1–§4 and §6 are implemented as an optional submodule
(`olinool_mcp/mcp_ext.py`) with tests and a runnable demo (`olinool-mcp/examples/`);
§5a is **reserved pending the attestation-model spec** (see §5a, §7). Load-bearing
spec claims verified against the RC text 2026-07-05 (§7 spec-verification log). Targets
the MCP 2026-07-28 release candidate; the spec finalizes 2026-07-28 and any detail may
still shift until then. Nothing here is published — private repo only until after
finalization and only on Srini's explicit go (§0.2). Sources are cited per section.

**Primary sources** (read 2026-07-04):
- Extensions framework: modelcontextprotocol.io/extensions/overview
- Base protocol (statelessness, `_meta`, error codes): modelcontextprotocol.io/specification/draft/basic/index
- Authorization (OAuth 2.1 resource-server model): modelcontextprotocol.io/specification/draft/basic/authorization
- RC announcement: blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/

---

## 0. Decisions log (Srini, 2026-07-04 — all six original open questions resolved)

1. **Vendor prefix: `io.github.codebysrini`** — maps to a namespace he controls.
   Revisit only if a project domain materializes before any public SEP.
2. **Publication path: private prototype** until the spec finalizes 2026-07-28;
   evaluate an Extensions-Track SEP after. No early exposure — close gaps first.
   (The official track requires a reference implementation in an official SDK and a
   working-group association; spec: Creating Extensions §Requirements.)
3. **Result records over MCP: YES, as an OPTIONAL capability** — server MAY attach a
   signed `olinool-result` in the tool result's `_meta` (§5a).
4. **JSON-RPC error code: `-31000` confirmed** (§3).
5. **Receiver identity: split by transport.** HTTP servers = RFC 8707 canonical
   resource URI. stdio servers = the server's registered agent id (did:web / did:key)
   exactly as in the A2A binding — identity is the key, the id is its label; no URI
   needed (§2).
6. **Replay cache: MUST within a single verifier instance** for the invocation TTL;
   **SHOULD** share across instances; **MUST document** the deployment's replay
   window. Unenforceable MUSTs make honest implementations non-conformant — we don't
   write those (§2).

---

## 1. Extension identity

Per the Extensions framework (extensions/overview): id format
`{vendor-prefix}/{extension-name}`, reverse-DNS vendor prefix, name rules follow
`_meta` key naming.

- **Id:** `io.github.codebysrini/olinool` (prefix decided 2026-07-04, §0.1; name uses
  the locked name of the receipt-chain concept — no new names).
- **Version:** none in the id. Per spec guidance, evolution happens via capability
  flags/versioning inside the settings object, and any breaking change takes a NEW id
  (e.g. `<vendor-prefix>/olinool-v2`). We go further (§4): the settings object is
  **empty by design** in v0.1, so there is nothing to version in-band at all. The
  artifact profile (`v":"0.1"`, Ed25519-only) is carried and enforced by the artifacts
  themselves, never by transport metadata.
- **Repository/status:** third-party extension, prototyped privately in this repo
  until the spec finalizes 2026-07-28 (§0.2); `experimental-ext-*`/`ext-*` repos are
  for extensions inside the MCP org only.

## 2. Envelope binding

MCP `tools/call` already carries `params.name` (tool) and `params.arguments`. The
olinool-mcp envelope `{tool, arguments, chain, invocation}` therefore maps onto MCP
with ZERO new top-level fields: the two olinool artifacts ride in the request's
`_meta` under the extension's single key, per the `_meta` key format rules
(specification/draft/basic/index §General fields):

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {"q": "acme filings"},
    "_meta": {
      "io.github.codebysrini/olinool": {
        "chain": ["<receipt JWS>", "..."],
        "invocation": "<invocation JWS>"
      }
    }
  }
}
```

**Normative request binding (restated verbatim from olinool-mcp/README, pinned v0.2):**

    request_bytes = canonical_json({"tool": tool_name, "arguments": arguments})

using moolam's RFC 8785 JCS, where `tool_name` = `params.name` and `arguments` =
`params.arguments`. Both sides derive the bytes independently; the invocation's `req`
hash binds them. No serialized request bytes are ever shipped.

**Receiver identity (decided, §0.5):** `receiver_id` (the invocation `aud` and
leaf-`aud` match target, R11) is transport-split:
- **HTTP servers:** the server's canonical URI per the authorization spec's Canonical
  Server URI section (RFC 8707 resource identifier, e.g. `https://mcp.example.com/mcp`).
  The olinool audience and the OAuth token audience become the same string for the
  same endpoint — two independent bindings to one identity.
- **stdio servers:** the server's registered agent id (did:web / did:key), exactly as
  in the A2A binding — identity is the key, the id is its label; no URI needed.

**Statelessness fit:** the RC's stateless core requires every request to be
self-contained (basic/index §Statelessness). A chain + fresh invocation per call IS
per-request self-containment — no session state, no handshake dependency. The one
receiver-side state is the R12 nonce cache, which is security state (like any replay
cache), not protocol conversation state. Normative stance (decided, §0.6): a verifier
instance **MUST** maintain the nonce cache for at least the invocation TTL window;
horizontally scaled deployments **SHOULD** share the cache across instances and
**MUST document** the deployment's effective replay window. (No unenforceable MUSTs.)

## 3. Guard placement and error mapping

**Placement:** server-side, at `tools/call` ingress, before the tool executes —
`guard` is the gate (verify at the door, instinct 4). The five-step ingress check:

1. Extract `chain` + `invocation` from `_meta["<vendor-prefix>/olinool"]`; derive
   `request_bytes` per §2 from the request's own `name`/`arguments`.
2. `verify_chain` — R1–R10 (structure, signatures, root anchoring, linkage, parent
   hashes, monotonic scope, nested windows, depth, epoch, assurance).
3. R11 audience: leaf `aud` patterns and invocation `aud` vs `receiver_id`.
4. R12 possession: leaf-subject signature, receipt + request hash binding, freshness
   window, nonce unseen.
5. Tool→grant check: `grant_permits(effective_scope, "call", "tool/<name>")` — the
   pinned convention from olinool-mcp/README.

(Steps 2–4 are one `verify_invocation` call; step 5 is the wedge's scope gate. This is
`olinool_mcp.guard` unchanged — the extension adds carriage, not semantics.)

**Error mapping.** A denial is a protocol-level refusal BEFORE tool execution, so it is
a JSON-RPC error response, not a tool result with `isError` (which reports execution
failures). Per the spec's error-code allocation policy (basic/index §Error Codes:
implementation codes go OUTSIDE the JSON-RPC reserved range `-32768..-32000`;
`-32020..-32099` is spec-reserved — we must not squat there):

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "error": {
    "code": -31000,
    "message": "olinool: authorization denied",
    "data": {
      "error": "ERR_SCOPE_WIDENED",
      "detail": "hop 2: scope not a subset of parent scope"
    }
  }
}
```

- One transport code (`-31000`, confirmed §0.4) for ALL olinool denials; the closed
  `ERR_*` vocabulary rides in `data.error` untouched. Their taxonomy for transport,
  ours for meaning — the closed set stays closed (instinct 11).
- A request that advertises the extension but omits the `_meta` key on a guarded tool:
  same code, `data.error` = the package-local `ERR_TOOL_NOT_GRANTED`? **No** — absence
  of artifacts is not a scope decision; it maps to `data.error: "ERR_STRUCTURE"`
  (nothing verifiable presented, fail closed).
- **Layering vs OAuth:** the HTTP 401/403 vocabulary belongs to the transport
  authorization layer (MCP server as OAuth 2.1 resource server; authorization spec
  §Error Handling). olinool failures are NOT OAuth failures — the bearer token may be
  perfectly valid while the delegation chain is forged. The two layers answer
  different questions (OAuth: is this client connection authorized to talk to me;
  olinool: did a principal delegate authority for THIS specific call, attenuated,
  possessed, once) and MUST NOT be conflated in status codes. A server may enforce
  both; each fails with its own vocabulary.

## 4. Capability advertisement vs negotiation (the instinct-9 analysis)

AINTIRAM instinct 9 / MURAI: closed sets, pinned profiles, no in-band negotiation of
algorithms, formats, versions. The MCP Extensions framework negotiates the `extensions`
capability map at initialization. Are these in conflict?

**No — and the distinction is precise.** The `extensions` map is transport-level
*feature advertisement*: "this endpoint can parse the olinool envelope key at all."
It selects between CARRYING the artifacts and NOT carrying them (graceful degradation
per the framework: unsupported side → fall back or reject). It never selects among
artifact profiles, algorithms, or verification behaviors, because:

1. **The settings object is empty (`{}`) by design.** There are no knobs: no algorithm
   list, no profile selector, no version parameter. The framework itself says an empty
   settings object means "no settings" — we make emptiness normative for this
   extension.
2. **Verification is advertisement-independent.** The verifier applies the single
   pinned profile (Ed25519-only, `v:"0.1"`, closed error set) to whatever arrives.
   Nothing a peer advertises can widen, downgrade, or reconfigure what `guard`
   accepts — a receipt with `alg:"HS256"` dies at R1 regardless of any capability map
   (c20 doctrine). Downgrade is structurally impossible, not discouraged.
3. **Profile evolution stays out-of-band.** A future PQC profile (`olinool/2`,
   ML-DSA — SPEC §9b) would be a NEW extension id, not a settings flag — mirroring the
   framework's own breaking-change rule. Two ids may coexist; within each, exactly one
   profile. The transport chooses which envelope it can carry; it never chooses what a
   receipt is.

The residual gray zone we accept with eyes open: an attacker who controls capability
advertisement can cause *absence* (envelope not carried → call arrives ungoverned).
That is a deployment-policy question — a receiver that REQUIRES olinool rejects calls
without artifacts (fail closed, §3) — not a negotiation of the artifacts themselves.
Verdict: **no constitutional conflict.** If review disagrees with this reading of
instinct 9, that disagreement goes to Srini, not into a reinterpretation here.

## 5. What this extension does NOT do (honestly)

- **No key distribution.** `KeyResolver` is out of band (A2A Agent Cards /
  `.well-known` per SPEC §2). The extension never carries public keys.
- **No revocation transport.** TTL + epochs live in the artifacts; no revocation feed
  rides this extension.
- **No policy language.** No Datalog, no conditions — Biscuit/AIP own that ground.
  Scope algebra v0 only.
- **No OAuth replacement.** It layers UNDER transport auth (§3); it neither issues,
  validates, nor transports bearer tokens.
- **No mint-side transport.** How a caller OBTAINS a chain (delegation ceremonies)
  is out of scope; the extension moves and verifies, it does not mint.

### 5a. OPTIONAL capability: result records (decided IN §0.3; RESERVED pending spec)

**Status (2026-07-05): reserved pending the attestation-model spec — not implemented.**
The intent stands (§0.3: result records over MCP, optional), but the wire binding below
depends on a counter-signed result lane (`ver:"counter"`, attester = server) that
INVERTS `mint_result`'s `actor == leaf.sub` guard. Per the constitution (SPEC before
implementation), that attestation model — its mint path, its verify rules, its closed
errors, its corpus vectors — is written and frozen BEFORE any transport wiring. The
carriage layer (§2–§4, §6) ships without it; this capability is simply not advertised
until the spec lands. Deferred deliberately, not dropped.

> **⚠ Naming SURFACED to Srini, not resolved here.** The spec task
> `olinool/RESULT_ATTESTATION_TODO.md` (deferral of 2026-07-04) finds that this
> section's `ver:"counter"` label **collides with AIP's L2** (where "counter" =
> the *delegator* co-signs — a different actor) and that the MCP-server case is a
> *third* role, **receiver-attested** (the executor, which is NOT in the delegation
> chain), distinct from both `self` and a true delegator-countersign. The `ver:"counter"`
> naming in the prose below is therefore **provisional and under revision** by that
> task; the final `ver` values are Srini's to freeze (one concept, one name — MURAI).
> Per hard rule 1, this draft flags the conflict rather than reinterpreting it.

A server implementing this extension **MAY** close the authority→action loop over the
same transport: after executing a guarded tool call, attach a signed `olinool-result`
(SPEC §14) to the tool result's `_meta` under the same extension key:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "resultType": "complete",
    "content": [{"type": "text", "text": "..."}],
    "_meta": {
      "io.github.codebysrini/olinool": {"result": "<olinool-result JWS>"}
    }
  }
}
```

Bindings: `rcp` = the presented leaf receipt, `inv` = the invocation from the request
(the exact-request link), `out` = sha256 of the tool's output bytes, `sub` = signed by
the SERVER'S agent identity. Note the actor inversion vs SPEC §14's default: here the
attester is the receiver/executor, not the leaf subject — this is the `ver:"counter"`
lane (receiver counter-attestation), not `ver:"self"`. `[design note: mint_result`
currently guards `actor == leaf.sub`; a counter-signed variant needs its own mint path
and its own verify rules — spec work before code, per the constitution.]` Optionality
is capability-advertised implicitly by presence in responses; clients that ignore
`_meta` lose nothing (graceful degradation).

## 6. Relationship to existing artifacts

`olinool-mcp` (the wedge) already implements the semantic core: `wrap_call` =
mint-on-egress (client side), `guard` = §3 steps 2–5 (server side). The extension is
carriage + conventions only: `_meta` key (§2), receiver-id rule (§2), error surface
(§3), capability entry (§4). The reversibility test (AINTIRAM §3) passes: delete this
extension and every primitive — receipts, invocations, results, the corpus — survives
untouched. Transports are ridden, never built (instinct 12).

## 7. Spec-verification log (2026-07-05)

Load-bearing claims checked against the live RC spec text (fetched 2026-07-05):
`specification/draft/basic/index` and `extensions/overview`. Each is marked
`[confirmed <spec-section>]` or `[diverges — surfaced]`. **Result: all four
load-bearing claims confirmed; zero divergences; no constitutional conflict.**

1. **`_meta` as sanctioned extension carriage — [confirmed: basic/index §General
   fields → `_meta`].** "The `_meta` property/parameter is reserved by MCP to allow
   clients and servers to attach additional metadata to their interactions." Key format
   verified for our id: prefix labels start with a letter / end alnum (`io`, `github`,
   `codebysrini` all pass); a prefix is MCP-reserved only if its **second** label is
   `modelcontextprotocol`/`mcp` — ours is `github`, so `io.github.codebysrini/olinool`
   is a legal, non-reserved key. **Stronger than assumed:** `_meta` is now *mandatory*
   per request — every `tools/call` MUST already carry `io.modelcontextprotocol/*`
   protocol fields in `_meta`. Our envelope is an additional key alongside them; no
   collision. Confirms the §2 decision to keep `request_bytes` over name+arguments ONLY
   (never `_meta`): the mandatory protocol fields and the envelope itself correctly sit
   outside the signed bytes.
2. **JSON-RPC error code `-31000` — [confirmed: basic/index §Error Codes].** Spec:
   "New error codes … **SHOULD** be allocated outside the JSON-RPC reserved range
   (`-32768` to `-32000`)." `-31000 > -32000`, so it is outside the reserved range.
   The spec-reserved implementation band is now explicit and narrower than the draft's
   earlier guess: `-32000..-32019` legacy, **`-32020..-32099` reserved for the MCP
   spec**. `-31000` is clear of both. Compliant, unchanged.
3. **Extensions framework — [confirmed: extensions/overview §Negotiation, §Evolution].**
   Id format `{vendor-prefix}/{extension-name}`, third-party uses a reversed domain it
   owns (✓ §1). `extensions` capability map advertised in the `initialize`
   request/response (✓ §4). Empty settings semantics verbatim: "an empty object
   indicates no settings" — makes our empty-`{}`-by-design normative (✓ §4.1). Graceful
   degradation verbatim: the supporting side "needs to either fall back to core protocol
   behavior or reject the request … if the extension is mandatory" (✓ §3/§4 fail-closed).
   Breaking-change rule verbatim: "If a breaking change is unavoidable, use a new
   identifier (e.g., `…/my-extension-v2`)" — matches §1/§4.3 exactly. Also noted:
   "Extensions are always disabled by default and require explicit opt-in" — reinforces
   §4's graceful-degradation stance and the §0.2 private-prototype posture.
4. **Statelessness — [confirmed: basic/index §Statelessness].** Verbatim: "MCP is a
   **stateless protocol**: all the information needed to process a request is contained
   in the request itself. A server processes each request independently; no state should
   be inferred from previous requests." A chain + fresh invocation per call IS
   per-request self-containment (✓ §2). The R12 nonce cache does not violate this: the
   statelessness rule forbids inferring *protocol context* (capabilities, version,
   identity) from prior requests; a replay cache infers no context — it only rejects
   duplicates. It is security state, exactly as §2 framed it. No divergence.

**Adjacent confirmations (not among the four, noted in passing):**
- Result responses now REQUIRE a `resultType` field (`"complete"` / `"input_required"`);
  the §5a example already carries `"resultType": "complete"` — consistent, no change.
- HTTP-vs-stdio auth split (§2 receiver-id, §3 layering) is consistent with the spec:
  auth framework is HTTP-only; "implementations using STDIO transport **SHOULD NOT**
  follow this specification, and instead retrieve credentials from the environment" —
  supports the transport-split receiver identity and the olinool-is-not-OAuth layering.
- Official Extensions-Track SEP requires a reference implementation in an official SDK
  **and** a working/interest-group association (extensions/overview §Creating Extensions
  §Requirements). This private prototype is not on that track yet — matches §0.2.

**Implementation status by section:** §1 (identity) ✓ implemented · §2 (envelope
binding) ✓ · §3 (guard placement + `-31000` error mapping) ✓ · §4 (capability /
no-negotiation) ✓ (analysis holds against confirmed framework) · §5 (non-goals) n/a ·
**§5a (result records) — reserved pending the attestation-model spec** · §6 (carriage,
not semantics; reversibility) ✓. Code: `olinool-mcp/python/olinool_mcp/mcp_ext.py`
(`attach_envelope`, `guard_request`, `denial_to_jsonrpc_error`); tests
`python/tests/test_mcp_ext.py` (7); demo `examples/mcp_server_demo.py`. `mcp` SDK is an
optional extra; core imports and the guard path run without it.
