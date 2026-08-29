#!/usr/bin/env node
// build-evidence.cjs — assemble an evidence bundle for a completed
// workstream: one schema-valid evidence.schema.json instance per item,
// written as individual files under an output directory. Stdlib Node
// only, no node_modules.
//
// Usage:
//   node build-evidence.cjs --workstream-id <id> --out <dir> \
//     --item kind=test,subject="unit tests",uri=<path>,result=pass \
//     --item kind=lint,subject="lint",uri=<path>,result=pass
//
// A "bundle" here is a directory of evidence-item JSON files, each tagged
// "$schemaRef": "evidence" — the same convention validate-contracts.cjs
// already reads for any examples directory. Point it at the output dir to
// gate the bundle: `node validate-contracts.cjs <out-dir>`.
//
// Each --item is a comma-separated key=value list:
//   kind=<diff|build|lint|typecheck|test|policy_decision|approval|
//         effect_receipt|evaluation|recovery|other>   required
//   subject=<text>                                     required
//   uri=<path-or-uri-reference>                         required
//   result=<pass|fail|informational>                   required
//   id=<evidence-id>            default: evidence:<workstream slug>-<NN>-<kind>
//   independent=<true|false>
//   classification=<public|internal|confidential|restricted>  default internal
//   content-in-trace=<true|false>                       default false
//   activity-id=<id>            default: activity:<workstream slug>-<NN>
//
// If `uri` resolves to a readable file (relative to cwd or absolute), its
// bytes are hashed for content_hash. Otherwise the uri string itself is
// hashed — the item still validates, but is not proof a real artifact
// exists on disk; prefer real file paths for anything gating a HANDOFF.
//
// Options:
//   --workstream-id <id>     required
//   --job-id <id>             default: job:<workstream slug>
//   --producer-id <id>        default: agent:feature-lead
//   --producer-type <t>       human | agent | workload | service (default agent)
//   --producer-name <s>
//   --generated-at <ts>       default: now (ISO 8601 UTC), shared by all items
//   --schema-version <v>      default 1.0.0
//   --out <dir>               required; bundle directory (created if absent)

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DEFAULTS = {
  schemaVersion: '1.0.0',
  producerId: 'agent:feature-lead',
  producerType: 'agent',
  classification: 'internal',
};

function idSlug(id) {
  const value = String(id).includes(':') ? String(id).split(':').slice(1).join(':') : String(id);
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'workstream';
}

function parseItemSpec(spec) {
  const item = {};
  for (const pair of spec.split(',')) {
    const eq = pair.indexOf('=');
    if (eq === -1) throw new Error(`--item entry missing '=': ${pair}`);
    const key = pair.slice(0, eq).trim();
    const value = pair.slice(eq + 1).trim();
    item[key] = value;
  }
  return item;
}

function hashUri(uri) {
  const candidate = path.resolve(uri);
  if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
    const bytes = fs.readFileSync(candidate);
    return `sha256:${crypto.createHash('sha256').update(bytes).digest('hex')}`;
  }
  return `sha256:${crypto.createHash('sha256').update(uri, 'utf8').digest('hex')}`;
}

function parseArgv(argv) {
  const options = {
    schemaVersion: DEFAULTS.schemaVersion,
    producerId: DEFAULTS.producerId,
    producerType: DEFAULTS.producerType,
    items: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    switch (arg) {
      case '--workstream-id': options.workstreamId = next(); break;
      case '--job-id': options.jobId = next(); break;
      case '--producer-id': options.producerId = next(); break;
      case '--producer-type': options.producerType = next(); break;
      case '--producer-name': options.producerName = next(); break;
      case '--generated-at': options.generatedAt = next(); break;
      case '--schema-version': options.schemaVersion = next(); break;
      case '--out': options.out = next(); break;
      case '--item': options.items.push(parseItemSpec(next())); break;
      case '-h':
      case '--help': options.help = true; break;
      default:
        throw new Error(`unknown flag: ${arg}`);
    }
  }
  return options;
}

const USAGE = [
  'Usage: node build-evidence.cjs --workstream-id <id> --out <dir> --item kind=...,subject=...,uri=...,result=... [--item ...]',
  '',
  'See the file header for the full --item key list and defaults.',
].join('\n');

const VALID_KINDS = new Set([
  'diff', 'build', 'lint', 'typecheck', 'test', 'policy_decision',
  'approval', 'effect_receipt', 'evaluation', 'recovery', 'other',
]);
const VALID_RESULTS = new Set(['pass', 'fail', 'informational']);

function buildBundle(options) {
  if (!options.workstreamId) throw new Error('--workstream-id is required');
  if (!options.out) throw new Error('--out is required');
  if (options.items.length === 0) throw new Error('at least one --item is required');

  const slug = idSlug(options.workstreamId);
  const jobId = options.jobId || `job:${slug}`;
  const generatedAt = options.generatedAt || new Date().toISOString();

  const producer = {
    principal_id: options.producerId,
    principal_type: options.producerType,
  };
  if (options.producerName) producer.display_name = options.producerName;

  const documents = [];
  options.items.forEach((item, index) => {
    const ordinal = String(index + 1).padStart(2, '0');
    if (!item.kind || !VALID_KINDS.has(item.kind)) {
      throw new Error(`item ${ordinal}: kind must be one of ${[...VALID_KINDS].join(', ')}`);
    }
    if (!item.subject) throw new Error(`item ${ordinal}: subject is required`);
    if (!item.uri) throw new Error(`item ${ordinal}: uri is required`);
    if (!item.result || !VALID_RESULTS.has(item.result)) {
      throw new Error(`item ${ordinal}: result must be one of ${[...VALID_RESULTS].join(', ')}`);
    }

    const evidenceId = item.id || `evidence:${slug}-${ordinal}-${item.kind}`;
    const activityId = item['activity-id'] || `activity:${slug}-${ordinal}`;

    const document = {
      $schemaRef: 'evidence',
      schema_version: options.schemaVersion,
      evidence_id: evidenceId,
      job_id: jobId,
      workstream_id: options.workstreamId,
      kind: item.kind,
      producer,
      generated_at: generatedAt,
      subject: item.subject,
      uri: item.uri,
      content_hash: hashUri(item.uri),
      result: item.result,
      redaction: {
        classification: item.classification || DEFAULTS.classification,
        content_in_trace: item['content-in-trace'] === 'true',
      },
      provenance: {
        activity_id: activityId,
      },
    };
    if (item.independent !== undefined) document.independent = item.independent === 'true';

    documents.push({ evidenceId, ordinal, kind: item.kind, document });
  });

  return documents;
}

function main() {
  let options;
  try {
    options = parseArgv(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    console.error(USAGE);
    process.exit(2);
  }
  if (options.help) {
    console.log(USAGE);
    return;
  }

  let documents;
  try {
    documents = buildBundle(options);
  } catch (error) {
    console.error(error.message);
    console.error(USAGE);
    process.exit(2);
  }

  const outDir = path.resolve(options.out);
  fs.mkdirSync(outDir, { recursive: true });
  for (const { ordinal, kind, document } of documents) {
    const slug = kind.replace(/[^a-z0-9]+/g, '-');
    const outPath = path.join(outDir, `${ordinal}-${slug}.json`);
    fs.writeFileSync(outPath, `${JSON.stringify(document, null, 2)}\n`, 'utf8');
    console.log(`${document.evidence_id} -> ${outPath}`);
  }
}

main();
