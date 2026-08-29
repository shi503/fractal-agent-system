#!/usr/bin/env node
// Resolves a permission/version/hash/freshness-checked context bundle for a
// work contract. Stdlib Node only.

'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const fixture = JSON.parse(
  fs.readFileSync(path.join(root, 'examples', 'fixtures', 'graph-demo-bundle.json'), 'utf8')
);

function resolveBundle(contract, artifacts, principalId, resolvedAt) {
  const now = new Date(resolvedAt);
  if (Number.isNaN(now.getTime())) throw new Error('resolvedAt must be an ISO date-time');

  const resolved = contract.context.map((reference) => {
    const artifact = artifacts.find((candidate) => candidate.context_id === reference.id);
    if (!artifact) throw new Error(`Missing context artifact ${reference.id}`);
    if (artifact.version !== reference.version)
      throw new Error(`Version mismatch for ${reference.id}`);
    if (artifact.content_hash !== reference.content_hash)
      throw new Error(`Hash mismatch for ${reference.id}`);
    if (artifact.valid_from && now < new Date(artifact.valid_from)) {
      throw new Error(`Context artifact ${reference.id} is not yet valid`);
    }
    if (artifact.expires_at && now >= new Date(artifact.expires_at)) {
      throw new Error(`Context artifact ${reference.id} is expired`);
    }
    if (now >= new Date(artifact.review_by)) {
      throw new Error(`Context artifact ${reference.id} is overdue for review`);
    }
    if (artifact.permitted_principals && !artifact.permitted_principals.includes(principalId)) {
      throw new Error(`Principal ${principalId} is not permitted to use ${reference.id}`);
    }
    return {
      id: artifact.context_id,
      version: artifact.version,
      uri: artifact.uri,
      content_hash: artifact.content_hash,
      owner: artifact.owner,
      classification: artifact.classification,
    };
  });

  return {
    bundle_version: '1.0.0',
    bundle_id: `context_bundle:${contract.workstream_id.split(':')[1]}-fixture`,
    job_id: contract.job_id,
    workstream_id: contract.workstream_id,
    principal_id: principalId,
    purpose: 'execute-work-contract',
    resolved_at: now.toISOString(),
    artifacts: resolved.sort((a, b) => a.id.localeCompare(b.id)),
    conflicts: [],
  };
}

const validTime = '2026-08-20T18:00:00Z';
const bundle = resolveBundle(
  fixture.workContract,
  [fixture.contextArtifact],
  fixture.workContract.assigned_to.principal_id,
  validTime
);
console.log(
  `Context bundle valid: ${bundle.bundle_id}, ${bundle.artifacts.length} authorized artifact(s).`
);

for (const test of [
  {
    name: 'unauthorized principal',
    principal: 'agent:unapproved',
    time: validTime,
    expected: /not permitted/,
  },
  {
    name: 'overdue artifact',
    principal: fixture.workContract.assigned_to.principal_id,
    time: '2026-10-01T00:00:00Z',
    expected: /overdue for review/,
  },
]) {
  let rejected = false;
  try {
    resolveBundle(fixture.workContract, [fixture.contextArtifact], test.principal, test.time);
  } catch (error) {
    rejected = test.expected.test(error.message);
  }
  if (!rejected) throw new Error(`${test.name} fixture was not rejected`);
  console.log(`${test.name} fixture: rejected as expected.`);
}

if (process.argv.includes('--json')) console.log(JSON.stringify(bundle, null, 2));
