/**
 * olinool ayadi verifier — TypeScript port of the reference implementation
 * (olinool/python/olinool/ayadi.py + scopes.py + result.py + profiles/).
 *
 * Scope: VERIFICATION ONLY (rules R1–R12 and result records, same closed
 * error codes as olinool/SPEC.md §5–§7, §14). Two profiles are decoded:
 * jws-1 (compact JWS, the frozen v0.1 wire) and sd-1 (SD-JWT combined form,
 * RFC 9901 — SPEC §16; disclosure-digest verification only, no KB-JWT). A
 * verifier never canonicalizes — it consumes fixed JWS bytes and the
 * disclosure strings exactly as presented — so no RFC 8785 code exists here
 * on purpose. Minting in TypeScript is out of scope for v0.2 and would
 * require byte-parity JCS work; do not add it casually.
 *
 * Certified against ../olinool/python/olinool/conformance/vectors (see test/corpus.test.ts).
 */
import * as ed from '@noble/ed25519';
import { sha256 } from '@noble/hashes/sha256';
import { sha512 } from '@noble/hashes/sha512';

// noble's sync verify needs a sha512 implementation wired in.
ed.etc.sha512Sync = (...m: Uint8Array[]) => sha512(ed.etc.concatBytes(...m));

export const VERSION = '0.1';
export const RECEIPT_TYP = 'olinool-receipt+jws';
export const INVOCATION_TYP = 'olinool-invocation+jws';
export const RESULT_TYP = 'olinool-result+jws';
// sd-1 (SD-JWT, SPEC §16) typ markers + the pinned disclosure-hash algorithm.
export const SD_RECEIPT_TYP = 'olinool-receipt+sd-jwt';
export const SD_INVOCATION_TYP = 'olinool-invocation+sd-jwt';
export const SD_RESULT_TYP = 'olinool-result+sd-jwt';
export const SD_ALG = 'sha-256'; // pinned (§16.1); any other value is structural failure (instinct 9)

// Closed error set — conformance vectors assert on these exact strings.
export const ERR_STRUCTURE = 'ERR_STRUCTURE';
export const ERR_SIG = 'ERR_SIG';
export const ERR_ROOT_UNTRUSTED = 'ERR_ROOT_UNTRUSTED';
export const ERR_LINKAGE = 'ERR_LINKAGE';
export const ERR_PARENT_HASH = 'ERR_PARENT_HASH';
export const ERR_SCOPE_WIDENED = 'ERR_SCOPE_WIDENED';
export const ERR_TIME_NOT_NESTED = 'ERR_TIME_NOT_NESTED';
export const ERR_EXPIRED = 'ERR_EXPIRED';
export const ERR_DEPTH = 'ERR_DEPTH';
export const ERR_REVOKED_EPOCH = 'ERR_REVOKED_EPOCH';
export const ERR_ASSURANCE = 'ERR_ASSURANCE';
export const ERR_AUDIENCE = 'ERR_AUDIENCE';
export const ERR_POP = 'ERR_POP';
export const ERR_REPLAY = 'ERR_REPLAY';
export const ERR_RESULT_STRUCTURE = 'ERR_RESULT_STRUCTURE';
export const ERR_RESULT_SIG = 'ERR_RESULT_SIG';
export const ERR_RESULT_BINDING = 'ERR_RESULT_BINDING';
export const ERR_PROFILE_NOT_ALLOWED = 'ERR_PROFILE_NOT_ALLOWED';
export const ERR_PROFILE_MIXED = 'ERR_PROFILE_MIXED';

// ---------------------------------------------------------------- encoding

export function b64uDecode(s: string): Uint8Array {
  return new Uint8Array(Buffer.from(s, 'base64url'));
}

export function b64uEncode(data: Uint8Array): string {
  return Buffer.from(data).toString('base64url');
}

export function sha256B64u(data: Uint8Array): string {
  return b64uEncode(sha256(data));
}

const utf8 = (s: string): Uint8Array => new Uint8Array(Buffer.from(s, 'utf-8'));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;

export interface DecodedJws {
  header: Json;
  payload: Json;
  signingInput: Uint8Array;
  sig: Uint8Array;
  /** The profile-defined R5 parent-hash preimage (SPEC §16.4). For jws-1 this
   * is the VERBATIM received string; for sd-1 it will be the issuer-signed
   * base (the JWT before holder-selected disclosures). Mirrors the Python
   * profile seam's `Decoded.artifact_bytes`. */
  artifactBytes: string;
}

/** Compact-JWS decode. Throws on malformed input (structure errors). */
export function jwsDecode(jws: string): DecodedJws {
  const parts = jws.split('.');
  if (parts.length !== 3) throw new Error('JWS must have three segments');
  const [h, p, s] = parts;
  const header = JSON.parse(Buffer.from(h, 'base64url').toString('utf-8'));
  const payload = JSON.parse(Buffer.from(p, 'base64url').toString('utf-8'));
  return { header, payload, signingInput: utf8(`${h}.${p}`), sig: b64uDecode(s), artifactBytes: jws };
}

// ------------------------------------------------- envelope families + codecs
// Mirror of olinool.profiles (envelope_of / decode_artifact / sd1 codec).
// Structural sniff: the SD-JWT combined form is `~`-delimited, and `~` can
// never appear in a compact JWS (base64url alphabet + '.'), so the family is
// decidable without reading any claim — nothing is negotiated.

export type Envelope = 'jws' | 'sd-jwt';

export function envelopeOf(artifact: string): Envelope {
  return artifact.includes('~') ? 'sd-jwt' : 'jws';
}

/** RFC 9901 disclosure parse: b64u(JSON [salt, claim_name, claim_value]).
 * Mirrors olinool.profiles.sd1._parse_disclosure — any failure is structural. */
function parseDisclosure(disclosure: string): [string, Json] {
  let arr: Json;
  try {
    arr = JSON.parse(Buffer.from(disclosure, 'base64url').toString('utf-8'));
  } catch (e) {
    throw new Error(`malformed disclosure: ${(e as Error).message}`);
  }
  if (!Array.isArray(arr) || arr.length !== 3 || typeof arr[0] !== 'string' || typeof arr[1] !== 'string') {
    throw new Error('disclosure must be [salt, claim_name, claim_value]');
  }
  return [arr[1], arr[2]];
}

/** Resolve `_sd` digest arrays against the presented disclosures, recursively
 * (structured claims, §16.2 — covers `asr.evidence`). Returns a resolved copy
 * with `_sd`/`_sd_alg` stripped; the data model never sees encoding
 * artifacts. A digest with no presented disclosure is simply withheld — R1b
 * fails closed later if the data model requires that claim. Mirrors
 * olinool.profiles.sd1._walk check for check. */
function sdWalk(
  obj: Json,
  byDigest: Map<string, string>,
  seenDigests: Set<string>,
  consumed: Set<string>,
  top = false,
): Json {
  if (Array.isArray(obj)) return obj.map((v) => sdWalk(v, byDigest, seenDigests, consumed));
  if (typeof obj !== 'object' || obj === null) return obj;
  if ('...' in obj) throw new Error("array-element disclosures ('...') are not part of sd-1");
  if ('_sd_alg' in obj) {
    if (!top) throw new Error('_sd_alg is top-level only (RFC 9901)');
    if (obj._sd_alg !== SD_ALG) throw new Error(`_sd_alg is pinned to '${SD_ALG}' (§16.1, no negotiation)`);
  }
  const out: Record<string, Json> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (k === '_sd' || k === '_sd_alg') continue;
    out[k] = sdWalk(v, byDigest, seenDigests, consumed);
  }
  const sd = (obj as Record<string, Json>)._sd ?? null;
  if (sd !== null) {
    if (!Array.isArray(sd) || !sd.every((x) => typeof x === 'string')) {
      throw new Error('_sd must be an array of digest strings');
    }
    for (const dig of sd) {
      if (seenDigests.has(dig)) throw new Error('duplicate digest in _sd');
      seenDigests.add(dig);
      const disclosure = byDigest.get(dig);
      if (disclosure === undefined) continue; // withheld by the holder — fail-closed at R1b if required
      const [name, value] = parseDisclosure(disclosure);
      if (name in out) throw new Error(`disclosure collides with existing claim '${name}'`);
      consumed.add(dig);
      out[name] = sdWalk(value, byDigest, seenDigests, consumed);
    }
  }
  return out;
}

/** sd-1 decode (SPEC §16.2, mirror of olinool.profiles.sd1._Sd1Profile.decode):
 * combined-form parse, base JWT parse + `alg==EdDSA`, pinned `_sd_alg`,
 * digest-checked disclosure resolution. Never checks typ/v (those are the
 * selection predicate). `artifactBytes` is the ISSUER-SIGNED BASE (§16.4) —
 * never the combined form — so a parent's hash is stable across
 * holder-selected disclosures. */
function sdJwtDecode(artifact: string): DecodedJws {
  if (!artifact.includes('~')) throw new Error('sd-1 artifact must be an SD-JWT combined form');
  if (!artifact.endsWith('~')) throw new Error("combined form must end with '~' (no KB-JWT, §16.1)");
  const segments = artifact.slice(0, -1).split('~');
  const base = segments[0];
  const presented = segments.slice(1);
  const { header, payload, signingInput, sig } = jwsDecode(base);
  if (header.alg !== 'EdDSA') throw new Error('alg must be EdDSA (single-algorithm policy)');

  const byDigest = new Map<string, string>();
  for (const d of presented) {
    const dig = sha256B64u(utf8(d));
    if (byDigest.has(dig)) throw new Error('duplicate disclosure presented');
    byDigest.set(dig, d);
  }
  const seenDigests = new Set<string>();
  const consumed = new Set<string>();
  const claims = sdWalk(payload, byDigest, seenDigests, consumed, true);
  for (const dig of byDigest.keys()) {
    if (!consumed.has(dig)) {
      throw new Error('presented disclosure matches no _sd digest (unknown or tampered disclosure)');
    }
  }
  if ((presented.length > 0 || seenDigests.size > 0) && payload._sd_alg !== SD_ALG) {
    throw new Error('_sd_alg missing or not sha-256 (§16.1)');
  }
  return { header, payload: claims, signingInput, sig, artifactBytes: base };
}

/** Family-codec dispatch (mirror of olinool.profiles.decode_artifact): sniff
 * the structural envelope, decode with that family's codec. Throws on any
 * envelope failure — the caller maps it to the slot's structural code
 * (ERR_STRUCTURE for receipts/results, ERR_POP for invocations). */
export function decodeArtifact(artifact: string): DecodedJws {
  if (envelopeOf(artifact) === 'sd-jwt') return sdJwtDecode(artifact);
  const d = jwsDecode(artifact);
  if (d.header.alg !== 'EdDSA') throw new Error('alg must be EdDSA (single-algorithm policy)');
  return d;
}

// ---------------------------------------------------------------- identity

/** Maps agent id -> Ed25519 public key (mirror of moolam.keys.KeyResolver). */
export class KeyResolver {
  private keys = new Map<string, Uint8Array>();

  register(agentId: string, publicKeyB64u: string): void {
    this.keys.set(agentId, b64uDecode(publicKeyB64u));
  }

  verify(agentId: string, data: Uint8Array, sig: Uint8Array): boolean {
    const key = this.keys.get(agentId);
    if (!key) return false;
    try {
      return ed.verify(sig, data, key);
    } catch {
      return false;
    }
  }
}

// ---------------------------------------------------------------- decision

export interface Decision {
  allowed: boolean;
  error: string | null;
  detail: string | null;
  effectiveScope: Grant[] | null;
}

const deny = (error: string, detail = ''): Decision =>
  ({ allowed: false, error, detail, effectiveScope: null });
const allow = (effectiveScope: Grant[]): Decision =>
  ({ allowed: true, error: null, detail: null, effectiveScope });

// ---------------------------------------------------------------- policy

export interface Policy {
  clockSkewS: number;
  invocationTtlS: number;
  minAssurance: number;
  maxChainLen: number;
  trustedPrincipals: Set<string> | null;
  currentEpoch: ((issuer: string) => number | null) | null;
  replayCache: Set<string>;
  allowedProfiles: Set<string>;
}

export function makePolicy(p: Partial<Policy> = {}): Policy {
  return {
    clockSkewS: p.clockSkewS ?? 60,
    invocationTtlS: p.invocationTtlS ?? 120,
    minAssurance: p.minAssurance ?? 0,
    maxChainLen: p.maxChainLen ?? 16,
    trustedPrincipals: p.trustedPrincipals ?? null,
    currentEpoch: p.currentEpoch ?? null,
    replayCache: p.replayCache ?? new Set(),
    allowedProfiles: p.allowedProfiles ?? new Set(['jws-1']),
  };
}

// ------------------------------------------------------------ profile seam
// §15 (v0.3): selection by the artifact's OWN (typ, v) markers, gated by the
// policy allow-list — never peer negotiation. Two profiles are registered
// (jws-1 and sd-1, same insertion order as the Python registry); this mirrors
// olinool.profiles.select_profile line for line, so a null here maps to
// ERR_PROFILE_NOT_ALLOWED before any claim logic runs. A profile is selected
// only when it is allowed, its structural envelope FAMILY matches the
// artifact's (the `~`-structure half of the REGISTRY predicate — a plain JWS
// re-tagged with sd-jwt typ markers can never select sd-1), AND its marker
// predicate matches: (typ, v) for receipts/results, typ alone for invocations
// (they carry no version claim).

interface ProfileDef {
  id: string;
  envelope: Envelope;
  receiptTyp: string;
  invocationTyp: string;
  resultTyp: string;
  version: string;
}

const PROFILE_REGISTRY: ProfileDef[] = [
  { id: 'jws-1', envelope: 'jws', receiptTyp: RECEIPT_TYP, invocationTyp: INVOCATION_TYP, resultTyp: RESULT_TYP, version: VERSION },
  { id: 'sd-1', envelope: 'sd-jwt', receiptTyp: SD_RECEIPT_TYP, invocationTyp: SD_INVOCATION_TYP, resultTyp: SD_RESULT_TYP, version: VERSION },
];

export function selectProfile(
  header: Json,
  claims: Json,
  allowed: Set<string>,
  envelope: Envelope = 'jws',
): string | null {
  for (const prof of PROFILE_REGISTRY) {
    if (!allowed.has(prof.id) || prof.envelope !== envelope) continue;
    const typ = header.typ;
    const matches =
      ((typ === prof.receiptTyp || typ === prof.resultTyp) && claims.v === prof.version) ||
      typ === prof.invocationTyp;
    if (matches) return prof.id;
  }
  return null;
}

// ------------------------------------------------------------ scope algebra
// Port of olinool.scopes — two implementations MUST compute the same subset
// answer or interop dies, so this follows the Python line by line.

export interface Grant {
  act: string;
  res: string;
  limits?: Record<string, number>;
}

export class ScopeError extends Error {}

const isPlainObject = (x: unknown): x is Record<string, Json> =>
  typeof x === 'object' && x !== null && !Array.isArray(x);

export function validateScope(scope: Json): void {
  if (!Array.isArray(scope) || scope.length === 0) {
    throw new ScopeError('scope must be a non-empty list of grants');
  }
  for (const g of scope) {
    if (!isPlainObject(g)) throw new ScopeError('grant must be an object');
    const extra = Object.keys(g).filter((k) => !['act', 'res', 'limits'].includes(k));
    if (extra.length) throw new ScopeError(`unknown grant fields: ${extra.sort().join(', ')}`);
    const { act, res } = g;
    if (typeof act !== 'string' || !act) throw new ScopeError('grant.act must be a non-empty string');
    if (typeof res !== 'string' || !res) throw new ScopeError('grant.res must be a non-empty string');
    const stars = (res.match(/\*/g) ?? []).length;
    if (stars > 1 || (stars === 1 && !res.endsWith('*'))) {
      throw new ScopeError(`grant.res may contain '*' only as final char: ${res}`);
    }
    const limits = g.limits ?? {};
    if (!isPlainObject(limits)) throw new ScopeError('grant.limits must be an object');
    for (const [k, v] of Object.entries(limits)) {
      if (typeof k !== 'string' || typeof v !== 'number' || Number.isNaN(v)) {
        throw new ScopeError('limits must map string keys to numbers');
      }
      if (v < 0) throw new ScopeError('limit values must be >= 0');
    }
  }
}

const actCovers = (parent: string, child: string): boolean =>
  parent === '*' || parent === child;

function resCovers(parent: string, child: string): boolean {
  if (parent.endsWith('*')) {
    const prefix = parent.slice(0, -1);
    if (child.endsWith('*')) return child.slice(0, -1).startsWith(prefix);
    return child.startsWith(prefix);
  }
  return parent === child; // literal parent covers only the identical literal
}

function limitsCover(parent: Record<string, number>, child: Record<string, number>): boolean {
  for (const [key, pval] of Object.entries(parent)) {
    if (!(key in child)) return false; // child unbounded where parent was bounded
    if (child[key] > pval) return false;
  }
  return true;
}

const grantCovers = (parent: Grant, child: Grant): boolean =>
  actCovers(parent.act, child.act) &&
  resCovers(parent.res, child.res) &&
  limitsCover(parent.limits ?? {}, child.limits ?? {});

export function isSubset(child: Grant[], parent: Grant[]): boolean {
  validateScope(child);
  validateScope(parent);
  return child.every((c) => parent.some((p) => grantCovers(p, c)));
}

// ---------------------------------------------------------------- fnmatch
// Tiny fnmatch-style matcher for leaf `aud` patterns (R11): *, ?, [seq].

export function fnmatchCase(name: string, pattern: string): boolean {
  let re = '';
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i];
    if (c === '*') re += '.*';
    else if (c === '?') re += '.';
    else if (c === '[') {
      let j = i + 1;
      let neg = false;
      if (pattern[j] === '!') { neg = true; j++; }
      if (pattern[j] === ']') j++;
      while (j < pattern.length && pattern[j] !== ']') j++;
      if (j >= pattern.length) {
        re += '\\[';
      } else {
        const stuff = pattern.slice(i + (neg ? 2 : 1), j).replace(/\\/g, '\\\\');
        re += `[${neg ? '^' : ''}${stuff}]`;
        i = j;
      }
    } else {
      re += c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
  }
  return new RegExp(`^${re}$`).test(name);
}

// ------------------------------------------------------ receipt structure

const REQUIRED_CLAIMS = ['v', 'rid', 'prh', 'pri', 'iss', 'sub', 'scope', 'cst', 'asr'];

function checkReceiptStructure(payload: Json): string | null {
  const missing = REQUIRED_CLAIMS.filter((k) => !(k in payload)).sort();
  if (missing.length) return `missing claims: ${missing.join(', ')}`;
  if (payload.v !== VERSION) return `unsupported version ${payload.v}`;
  const cst = payload.cst;
  if (!isPlainObject(cst)) return 'cst must be an object';
  for (const k of ['iat', 'exp', 'max_depth', 'epoch']) {
    if (!Number.isInteger(cst[k])) return `cst.${k} must be an integer`;
  }
  const asr = payload.asr;
  if (!isPlainObject(asr) || ![0, 1, 2].includes(asr.level)) return 'asr.level must be 0, 1, or 2';
  if ('aud' in payload &&
      (!Array.isArray(payload.aud) || !payload.aud.every((a: unknown) => typeof a === 'string'))) {
    return 'aud must be a list of strings';
  }
  try {
    validateScope(payload.scope);
  } catch (e) {
    return `scope: ${(e as Error).message}`;
  }
  return null;
}

// ------------------------------------------------------- chain verification

/** R1–R10: verify a Receipt chain root→leaf. No invocation binding yet. */
export function verifyChain(
  chain: string[],
  resolver: KeyResolver,
  policyIn: Partial<Policy> = {},
  now?: number,
): Decision {
  const policy = makePolicy(policyIn);
  const tNow = Math.trunc(now ?? Date.now() / 1000);

  if (!chain.length || chain.length > policy.maxChainLen) {
    return deny(ERR_STRUCTURE, 'empty chain or chain too long');
  }

  const decoded: Json[] = [];
  const raw: string[] = [];
  const profileIds: string[] = [];
  for (let idx = 0; idx < chain.length; idx++) {
    // R1a envelope (family codec via structural sniff): compact-JWS parse or
    // SD-JWT combined-form parse + disclosure-digest resolution (§16.2), each
    // with alg==EdDSA. Malformed / non-EdDSA / bad disclosure -> ERR_STRUCTURE.
    let d: DecodedJws;
    try {
      d = decodeArtifact(chain[idx]);
    } catch (e) {
      return deny(ERR_STRUCTURE, `hop ${idx}: ${(e as Error).message}`);
    }
    const { header, payload, signingInput, sig } = d;
    // Profile selection by the artifact's own markers within its structural
    // envelope family, gated by the allow-list — before any claim logic (§5)
    const pid = selectProfile(header, payload, policy.allowedProfiles, envelopeOf(chain[idx]));
    if (pid === null) {
      return deny(ERR_PROFILE_NOT_ALLOWED, `hop ${idx}: profile not in allow-list`);
    }
    // R1b claim schema
    const err = checkReceiptStructure(payload);
    if (err) return deny(ERR_STRUCTURE, `hop ${idx}: ${err}`);
    // R2 signature by claimed issuer
    if (header.kid !== payload.iss || !resolver.verify(payload.iss, signingInput, sig)) {
      return deny(ERR_SIG, `hop ${idx}: signature invalid for issuer ${payload.iss}`);
    }
    decoded.push(payload);
    // R5 preimage seam (SPEC §16.4): carry the PROFILE-decoded artifactBytes,
    // not the verbatim wire string. For jws-1 they are identical by definition
    // (frozen-corpus gate); for sd-1 this is the issuer-signed base, so a
    // parent's hash is stable across holder-selected disclosures.
    raw.push(d.artifactBytes);
    profileIds.push(pid);
  }

  // Uniform-profile rule (§5): all hops must share one profile.
  if (new Set(profileIds).size > 1) {
    return deny(ERR_PROFILE_MIXED, `chain mixes profiles: ${[...new Set(profileIds)].sort().join(', ')}`);
  }

  const root = decoded[0];
  // R3 root anchoring
  if (root.prh !== null || root.iss !== root.pri) {
    return deny(ERR_ROOT_UNTRUSTED, 'root must have prh=null and iss==pri');
  }
  if (policy.trustedPrincipals !== null && !policy.trustedPrincipals.has(root.pri)) {
    return deny(ERR_ROOT_UNTRUSTED, `principal ${root.pri} not trusted by policy`);
  }

  const n = decoded.length;
  for (let i = 1; i < n; i++) {
    const cur = decoded[i];
    const prev = decoded[i - 1];
    // R4 issuer/subject continuity + stable principal
    if (cur.iss !== prev.sub || cur.pri !== root.pri) {
      return deny(ERR_LINKAGE, `hop ${i}: issuer/principal continuity violated`);
    }
    // R5 parent hash binds exact bytes
    if (cur.prh !== sha256B64u(utf8(raw[i - 1]))) {
      return deny(ERR_PARENT_HASH, `hop ${i}: prh does not match parent receipt`);
    }
    // R6 monotonic scope attenuation
    try {
      if (!isSubset(cur.scope, prev.scope)) {
        return deny(ERR_SCOPE_WIDENED, `hop ${i}: scope not a subset of parent scope`);
      }
    } catch (e) {
      return deny(ERR_STRUCTURE, `hop ${i}: scope: ${(e as Error).message}`);
    }
    // R7 time windows nest
    if (cur.cst.iat < prev.cst.iat || cur.cst.exp > prev.cst.exp) {
      return deny(ERR_TIME_NOT_NESTED, `hop ${i}: window not nested in parent`);
    }
  }

  // R7b leaf window vs wall clock (nesting makes the leaf the tightest window)
  const leaf = decoded[n - 1];
  if (tNow > leaf.cst.exp + policy.clockSkewS) return deny(ERR_EXPIRED, 'leaf receipt expired');
  if (tNow < leaf.cst.iat - policy.clockSkewS) return deny(ERR_EXPIRED, 'leaf receipt not yet valid');

  // R8 depth: hops after i must not exceed hop i's declared max_depth
  for (let i = 0; i < n; i++) {
    if (n - 1 - i > decoded[i].cst.max_depth) {
      return deny(ERR_DEPTH, `hop ${i} allows ${decoded[i].cst.max_depth} further hops`);
    }
  }

  // R9 revocation epoch (optional online-ish signal; offline => TTL bounds risk)
  if (policy.currentEpoch !== null) {
    for (let i = 0; i < n; i++) {
      const required = policy.currentEpoch(decoded[i].iss);
      if (required !== null && decoded[i].cst.epoch < required) {
        return deny(ERR_REVOKED_EPOCH, `hop ${i}: epoch ${decoded[i].cst.epoch} < ${required}`);
      }
    }
  }

  // R10 assurance: chain level = min over hops
  const chainLevel = Math.min(...decoded.map((p) => p.asr.level));
  if (chainLevel < policy.minAssurance) {
    return deny(ERR_ASSURANCE, `chain assurance L${chainLevel} < required L${policy.minAssurance}`);
  }

  return allow(leaf.scope);
}

// -------------------------------------------------- invocation verification

/** R1–R12: full receiver-side check for one concrete request. */
export function verifyInvocation(
  chain: string[],
  invocationJws: string,
  requestBytes: Uint8Array,
  receiverId: string,
  resolver: KeyResolver,
  policyIn: Partial<Policy> = {},
  now?: number,
): Decision {
  const policy = makePolicy(policyIn);
  const tNow = Math.trunc(now ?? Date.now() / 1000);

  const chainDecision = verifyChain(chain, resolver, policy, tNow);
  if (!chainDecision.allowed) return chainDecision;
  // The chain is uniform-profile (verifyChain enforced §5); the leaf's profile
  // is the chain's profile. decodeArtifact cannot throw here: the chain just
  // passed verifyChain (mirrors ayadi.verify_invocation).
  const leafDec = decodeArtifact(chain[chain.length - 1]);
  const leaf = leafDec.payload;
  const chainProfile = selectProfile(
    leafDec.header, leaf, policy.allowedProfiles, envelopeOf(chain[chain.length - 1]),
  );

  // R11 audience
  if ('aud' in leaf && !leaf.aud.some((pat: string) => fnmatchCase(receiverId, pat))) {
    return deny(ERR_AUDIENCE, `receiver ${receiverId} not in leaf aud`);
  }

  // R12 proof of possession — envelope via the family codec (parse / non-EdDSA
  // / bad disclosure -> ERR_POP, as before), then the invocation MUST be an
  // allowed profile and the chain's profile (§5).
  let d: DecodedJws;
  try {
    d = decodeArtifact(invocationJws);
  } catch (e) {
    return deny(ERR_POP, `invocation: ${(e as Error).message}`);
  }
  const { header, payload: inv, signingInput, sig } = d;
  const invProfile = selectProfile(header, inv, policy.allowedProfiles, envelopeOf(invocationJws));
  if (invProfile === null) {
    return deny(ERR_PROFILE_NOT_ALLOWED, 'invocation profile not in allow-list');
  }
  if (invProfile !== chainProfile) {
    return deny(ERR_PROFILE_MIXED, 'invocation profile differs from chain profile');
  }
  if (inv.aud !== receiverId) return deny(ERR_AUDIENCE, 'invocation aud mismatch');
  // Leaf-binding preimage (SPEC §16.4): rcp binds the profile's artifactBytes
  // — for jws-1 the verbatim leaf wire string (identical to pre-sd-1
  // behavior), for sd-1 the issuer-signed base, stable across
  // holder-selected disclosures.
  if (inv.rcp !== sha256B64u(utf8(leafDec.artifactBytes))) {
    return deny(ERR_POP, 'invocation not bound to presented leaf receipt');
  }
  if (inv.req !== sha256B64u(requestBytes)) return deny(ERR_POP, 'invocation not bound to this request');
  if (inv.sub !== leaf.sub || header.kid !== leaf.sub) {
    return deny(ERR_POP, 'invocation signer is not the leaf subject');
  }
  if (!resolver.verify(leaf.sub, signingInput, sig)) return deny(ERR_POP, 'invocation signature invalid');
  if (!Number.isInteger(inv.iat) || Math.abs(tNow - inv.iat) > policy.invocationTtlS + policy.clockSkewS) {
    return deny(ERR_POP, 'invocation outside freshness window');
  }
  if (typeof inv.nnc !== 'string' || !inv.nnc) return deny(ERR_POP, 'invocation nonce missing');
  const cacheKey = `${leaf.sub}:${inv.nnc}`;
  if (policy.replayCache.has(cacheKey)) return deny(ERR_REPLAY, 'invocation nonce replayed');
  policy.replayCache.add(cacheKey);

  return allow(leaf.scope);
}

// ------------------------------------------------------ result verification

const RESULT_STATUSES = ['completed', 'failed', 'partial'];
const RESULT_VERIFICATION_LEVELS = ['self', 'counter', 'attested'];
const REQUIRED_RESULT_CLAIMS = ['v', 'typ', 'rid', 'rcp', 'inv', 'sub', 'status', 'out', 'ver', 'iat'];

/** Result records (§14): structure → signature → binding, first failure wins.
 * v0.3 (§5): result and leaf must share one allowed profile, checked before
 * the binding step — mirrors olinool.result.verify_result. */
export function verifyResult(
  resultJws: string,
  leafReceiptJws: string,
  resolver: KeyResolver,
  allowedProfiles?: Set<string>,
): Decision {
  const allowed = allowedProfiles ?? new Set(['jws-1']);
  let d: DecodedJws;
  try {
    d = jwsDecode(resultJws);
  } catch (e) {
    return deny(ERR_RESULT_STRUCTURE, `result parse: ${(e as Error).message}`);
  }
  const { header, payload, signingInput, sig } = d;
  if (header.alg !== 'EdDSA' || header.typ !== RESULT_TYP) return deny(ERR_RESULT_STRUCTURE, 'result: bad header');
  const missing = REQUIRED_RESULT_CLAIMS.filter((k) => !(k in payload)).sort();
  if (missing.length) return deny(ERR_RESULT_STRUCTURE, `missing claims: ${missing.join(', ')}`);
  if (payload.v !== VERSION || payload.typ !== 'olinool-result') {
    return deny(ERR_RESULT_STRUCTURE, 'unsupported version or typ');
  }
  if (!RESULT_STATUSES.includes(payload.status)) return deny(ERR_RESULT_STRUCTURE, `bad status ${payload.status}`);
  if (!RESULT_VERIFICATION_LEVELS.includes(payload.ver)) return deny(ERR_RESULT_STRUCTURE, `bad ver ${payload.ver}`);
  if (!Number.isInteger(payload.iat)) return deny(ERR_RESULT_STRUCTURE, 'iat must be an integer');
  for (const k of ['rid', 'rcp', 'sub', 'out']) {
    if (typeof payload[k] !== 'string' || !payload[k]) {
      return deny(ERR_RESULT_STRUCTURE, `${k} must be a non-empty string`);
    }
  }
  if (payload.inv !== null && typeof payload.inv !== 'string') {
    return deny(ERR_RESULT_STRUCTURE, 'inv must be a string or null');
  }

  if (header.kid !== payload.sub || !resolver.verify(payload.sub, signingInput, sig)) {
    return deny(ERR_RESULT_SIG, `signature invalid for sub ${payload.sub}`);
  }

  let leafDec: DecodedJws;
  try {
    leafDec = jwsDecode(leafReceiptJws);
  } catch (e) {
    return deny(ERR_RESULT_STRUCTURE, `leaf receipt parse: ${(e as Error).message}`);
  }
  const leaf = leafDec.payload;

  // Profile match (§5): result and leaf must share one allowed profile,
  // checked before binding. For jws-1 inputs this always holds. Mirrors
  // olinool.result.verify_result exactly, including the default 'jws'
  // envelope: result verification stays jws-1-practical until the sd-1
  // result mint ships (SPEC §16 status).
  const resultProfile = selectProfile(header, payload, allowed);
  const leafProfile = selectProfile(leafDec.header, leaf, allowed);
  if (resultProfile === null || leafProfile === null) {
    return deny(ERR_PROFILE_NOT_ALLOWED, 'result or leaf profile not in allow-list');
  }
  if (resultProfile !== leafProfile) {
    return deny(ERR_PROFILE_MIXED, 'result profile differs from leaf profile');
  }

  if (payload.sub !== leaf.sub) return deny(ERR_RESULT_BINDING, 'result signer is not the leaf subject');
  if (payload.rcp !== sha256B64u(utf8(leafReceiptJws))) {
    return deny(ERR_RESULT_BINDING, 'result not bound to presented leaf receipt');
  }

  return { allowed: true, error: null, detail: null, effectiveScope: null };
}
