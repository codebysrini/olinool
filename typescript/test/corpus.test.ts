/**
 * Corpus certification: the TypeScript verifier must reproduce
 * expect.allowed / expect.error EXACTLY for every vector in
 * ../olinool/python/olinool/conformance/vectors — same dispatch as olinool/conformance/run.py.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  KeyResolver,
  b64uDecode,
  verifyChain,
  verifyInvocation,
  verifyResult,
  type Policy,
} from '../src/verify.ts';

const corpusDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../olinool/python/olinool/conformance/vectors');
const files = readdirSync(corpusDir).filter((f) => f.endsWith('.json')).sort();

assert.ok(files.length >= 8, `expected the conformance corpus, found ${files.length} vectors`);

for (const file of files) {
  const v = JSON.parse(readFileSync(path.join(corpusDir, file), 'utf-8'));
  test(`${v.name} (expect ${v.expect.error ?? 'ALLOW'})`, () => {
    const resolver = new KeyResolver();
    for (const [agentId, pub] of Object.entries(v.keys)) resolver.register(agentId, pub as string);
    const policy: Partial<Policy> = {
      minAssurance: v.policy.min_assurance ?? 0,
      trustedPrincipals: v.policy.trusted_principals ? new Set<string>(v.policy.trusted_principals) : null,
      ...(v.policy.allowed_profiles ? { allowedProfiles: new Set<string>(v.policy.allowed_profiles) } : {}),
    };
    const now: number = v.policy.now;

    let d;
    if (v.result) {
      d = verifyResult(v.result, v.chain[v.chain.length - 1], resolver, policy.allowedProfiles);
    } else if (v.invocation) {
      d = verifyInvocation(
        v.chain, v.invocation, b64uDecode(v.request_b64), v.receiver_id, resolver, policy, now,
      );
    } else {
      d = verifyChain(v.chain, resolver, policy, now);
    }

    assert.equal(d.allowed, v.expect.allowed, `allowed mismatch (error=${d.error}, detail=${d.detail})`);
    assert.equal(d.error ?? null, v.expect.error, `error mismatch (detail=${d.detail})`);
  });
}
