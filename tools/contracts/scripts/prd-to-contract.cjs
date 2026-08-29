#!/usr/bin/env node
// prd-to-contract.cjs — derive a work-contract instance from a
// template-conformant workstream PRD. Stdlib Node only, no node_modules.
//
// Usage:
//   node prd-to-contract.cjs <prd.md> [<prd.md> ...] --out <dir> [options]
//
// Options:
//   --out <dir>              required; output directory (created if absent)
//   --risk-tier <R0..R4>     default R1
//   --repository <id>        default repo:taskflow
//   --requested-by <id>      default role:fractal-architect
//   --contract-version <v>   default 1.0.0
//   --schema-version <v>     default 1.0.0
//
// One JSON file per PRD, named after the PRD's parent directory
// (fixtures/taskflow/workstreams/a11y-audit/prd-a11y-audit.md -> a11y-audit.json).
//
// DETERMINISM CONTRACT
// The same PRD bytes always produce the same output bytes. There is no
// timestamp, hostname, random id, or directory listing anywhere in the
// emitted document: inputs come from argv in the order given, object keys
// are written in one fixed literal order, and every array that is
// semantically a set (paths, capabilities, evidence kinds, dependencies)
// is de-duplicated and sorted. Arrays that are semantically ordered
// (acceptance criteria, non-goals, context) keep the PRD's own document
// order, which is itself a property of the input bytes. The generation
// time is reported on stderr rather than stored, so a regenerated contract
// diffs clean against its committed copy.
//
// See tools/contracts/README.md, section "Integration with the markdown
// FRACTAL flow", for the field-by-field mapping and its known limits.

'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULTS = {
  schemaVersion: '1.0.0',
  contractVersion: '1.0.0',
  riskTier: 'R1',
  repository: 'repo:taskflow',
  requestedBy: 'role:fractal-architect',
  requestedByName: 'FRACTAL Architect',
};

// --- small text helpers -----------------------------------------------------

function stripEmphasis(text) {
  return text.replace(/`/g, '').replace(/\*\*/g, '').trim();
}

function slug(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// An `id` in common.schema.json is `<prefix>:<segment>` where the segment
// starts with an alphanumeric and may then contain A-Za-z0-9._~/- only.
function idSegment(text) {
  let out = text
    .replace(/[^A-Za-z0-9._~/-]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^[^A-Za-z0-9]+/, '')
    .replace(/[^A-Za-z0-9]+$/, '');
  if (out === '') out = 'unnamed';
  return out;
}

function sortedSet(values) {
  return Array.from(new Set(values)).sort();
}

function backtickedTokens(text) {
  const found = [];
  for (const match of text.matchAll(/`([^`]+)`/g)) found.push(match[1].trim());
  return found;
}

// --- PRD parsing ------------------------------------------------------------

function splitSections(lines) {
  const sections = [];
  let current = null;
  for (const line of lines) {
    const heading = /^##\s+(.*)$/.exec(line);
    if (heading) {
      current = { heading: heading[1].trim(), body: [] };
      sections.push(current);
      continue;
    }
    if (current) current.body.push(line);
  }
  return sections;
}

function findSection(sections, needle) {
  for (const section of sections) {
    const normalized = section.heading
      .toLowerCase()
      .replace(/^\d+\.\s*/, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (normalized.includes(needle)) return section.body;
  }
  return [];
}

function headerFields(lines) {
  const fields = new Map();
  for (const line of lines) {
    if (/^##\s+/.test(line)) break;
    const match = /^\*\*([^*:]+):\*\*\s*(.*)$/.exec(line.trim());
    if (match) fields.set(match[1].trim().toLowerCase(), match[2].trim());
  }
  return fields;
}

function firstParagraph(body) {
  const collected = [];
  for (const line of body) {
    const text = line.trim();
    if (text === '') {
      if (collected.length > 0) break;
      continue;
    }
    if (text.startsWith('>') || text.startsWith('---')) {
      if (collected.length > 0) break;
      continue;
    }
    if (text.startsWith('**') && text.includes(':**')) break;
    collected.push(text);
  }
  return stripEmphasis(collected.join(' '));
}

function bulletTexts(body) {
  const out = [];
  for (const line of body) {
    const match = /^\s*[-*]\s+(.+)$/.exec(line);
    if (!match) continue;
    const text = stripEmphasis(match[1]);
    if (text !== '') out.push(text);
  }
  return out;
}

// Both label spellings the PRD template and the fixture PRDs use:
//   **Read only:** `a`, `b`                     (colon inside the bold)
//   **Read only** (context — do not modify):    (colon and gloss outside)
function matchLabel(text) {
  const match = /^\*\*([^*]+?)\*\*\s*(?:\([^)]*\))?\s*:?\s*(.*)$/.exec(text);
  if (!match) return null;
  return {
    name: match[1].replace(/:\s*$/, '').replace(/\s*\([^)]*\)\s*$/, '').trim().toLowerCase(),
    rest: match[2],
  };
}

function labelledBullets(body, label) {
  const wanted = label.toLowerCase();
  const out = [];
  let active = false;
  for (const line of body) {
    const text = line.trim();
    const labelMatch = matchLabel(text);
    if (labelMatch) {
      active = labelMatch.name === wanted;
      if (active) {
        const inline = backtickedTokens(labelMatch.rest);
        for (const token of inline) out.push(token);
      }
      continue;
    }
    if (!active) continue;
    if (text === '') continue;
    const bullet = /^[-*]\s+(.+)$/.exec(text);
    if (!bullet) {
      active = false;
      continue;
    }
    const tokens = backtickedTokens(bullet[1]);
    out.push(...(tokens.length > 0 ? tokens : [stripEmphasis(bullet[1])]));
  }
  return out;
}

const MANIFEST_LABELS = {
  read: ['read only'],
  write: ['write / modify', 'write/modify', 'create'],
};

function parseManifest(body) {
  const buckets = { read: [], write: [] };
  let active = null;
  for (const line of body) {
    const text = line.trim();
    const labelMatch = matchLabel(text);
    if (labelMatch) {
      active = null;
      for (const [bucket, labels] of Object.entries(MANIFEST_LABELS)) {
        if (labels.includes(labelMatch.name)) active = bucket;
      }
      if (active) collectPaths(buckets[active], labelMatch.rest);
      continue;
    }
    if (!active) continue;
    if (text === '') continue;
    const bullet = /^[-*]\s+(.+)$/.exec(text);
    if (!bullet) {
      active = null;
      continue;
    }
    collectPaths(buckets[active], bullet[1]);
  }
  return { read: sortedSet(buckets.read), write: sortedSet(buckets.write) };
}

function collectPaths(target, text) {
  const tokens = backtickedTokens(text);
  const candidates = tokens.length > 0 ? tokens : [stripEmphasis(text)];
  for (const candidate of candidates) {
    const value = candidate.replace(/[.,;]+$/, '').trim();
    if (value === '' || value.toLowerCase() === 'none') continue;
    target.push(value);
  }
}

function fencedBlocks(body) {
  const blocks = [];
  let inside = false;
  let buffer = [];
  for (const line of body) {
    if (/^\s*```/.test(line)) {
      if (inside) {
        blocks.push(buffer.join('\n'));
        buffer = [];
      }
      inside = !inside;
      continue;
    }
    if (inside) buffer.push(line);
  }
  return blocks;
}

// Evidence kinds are read off the PRD's own CI-gate command block, so a
// workstream that never declares a gate never claims one.
const EVIDENCE_RULES = [
  [/\bbuild\b/i, 'build'],
  [/--noemit|\bmypy\b|\bpyright\b|go vet/i, 'typecheck'],
  [/\blint\b|eslint|\bruff\b|clippy|golangci/i, 'lint'],
  [/test:e2e|playwright|cypress/i, 'e2e'],
  [/\btest\b|vitest|\bjest\b|pytest|go test|cargo test/i, 'test'],
  [/migrat|prisma generate/i, 'migration'],
];

function evidenceKinds(gateText) {
  const kinds = [];
  for (const [pattern, kind] of EVIDENCE_RULES) {
    if (pattern.test(gateText)) kinds.push(kind);
  }
  return kinds.length > 0 ? sortedSet(kinds) : ['review'];
}

const TIER_CAPABILITIES = {
  haiku: 'cap:mechanical-edit',
  sonnet: 'cap:scoped-implementation',
  opus: 'cap:design-authority',
};

function parsePrd(prdPath) {
  const raw = fs.readFileSync(prdPath, 'utf8');
  const lines = raw.split('\n');
  const sections = splitSections(lines);
  const fields = headerFields(lines);

  const h1 = lines.find((line) => /^#\s+/.test(line)) || '';
  const titleMatch = /^#\s+PRD\s*[—–-]\s*(.+)$/.exec(h1.trim());
  const title = stripEmphasis(titleMatch ? titleMatch[1] : h1.replace(/^#\s+/, ''));

  const overview = findSection(sections, 'feature overview');
  const gateText = fencedBlocks(findSection(sections, 'ci gate')).join('\n');

  return {
    title,
    workstreamRef: stripEmphasis(fields.get('workstream id') || ''),
    modelTier: stripEmphasis(fields.get('model tier') || '').toLowerCase(),
    owner: stripEmphasis(fields.get('owner') || ''),
    dependsOn: stripEmphasis(fields.get('depends on') || '')
      .replace(/^\[|\]$/g, '')
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry !== ''),
    outcome: firstParagraph(overview),
    sourceDocuments: labelledBullets(overview, 'source documents'),
    acceptance: findSection(sections, 'acceptance criteria')
      .map((line) => /^\s*[-*]\s+\[[ xX]\]\s+(.+)$/.exec(line))
      .filter(Boolean)
      .map((match) => stripEmphasis(match[1]))
      .filter((text) => text !== ''),
    manifest: parseManifest(findSection(sections, 'file manifest')),
    gateText,
    nonGoals: bulletTexts(findSection(sections, 'out of scope')),
  };
}

// --- contract construction --------------------------------------------------

function principalFromOwner(owner) {
  const match = /\(([^)]+)\)/.exec(owner);
  if (!match) return null;
  const initials = match[1].trim();
  if (initials === '') return null;
  return {
    principal_id: `person:${idSegment(initials)}`,
    principal_type: 'human',
    display_name: owner,
  };
}

function buildAcceptance(descriptions, gateText) {
  const kinds = evidenceKinds(gateText);
  const used = new Map();
  return descriptions.map((description) => {
    const base = slug(description).slice(0, 60).replace(/-+$/, '') || 'criterion';
    const seen = (used.get(base) || 0) + 1;
    used.set(base, seen);
    const suffix = seen > 1 ? `-${seen}` : '';
    return {
      criterion_id: `criterion:${base}${suffix}`,
      description,
      evidence_kinds: kinds,
    };
  });
}

// A PRD names paths, never the repository they live in, so the repository id
// is supplied rather than derived. The default matches this repo's fixture
// corpus; pass --repository elsewhere.
function buildScope(manifest, repository) {
  const scope = [];
  if (manifest.read.length > 0) {
    scope.push({ repository_id: repository, access: 'read', paths: manifest.read });
  }
  if (manifest.write.length > 0) {
    scope.push({ repository_id: repository, access: 'write', paths: manifest.write });
  }
  return scope;
}

function buildCapabilities(prd) {
  const capabilities = ['cap:read-repository'];
  if (prd.manifest.write.length > 0) capabilities.push('cap:edit-isolated-repository');
  const tierCapability = TIER_CAPABILITIES[prd.modelTier];
  if (tierCapability) capabilities.push(tierCapability);
  return sortedSet(capabilities);
}

function buildContract(prd, jobSlug, options) {
  const contract = {
    $schemaRef: 'work-contract',
    schema_version: options.schemaVersion,
    contract_version: options.contractVersion,
    job_id: `job:${idSegment(jobSlug)}`,
    workstream_id: `workstream:${idSegment(prd.workstreamRef.toLowerCase() || jobSlug)}`,
    title: prd.title,
    outcome: prd.outcome,
    requested_by: {
      principal_id: options.requestedBy,
      principal_type: 'human',
      display_name: options.requestedByName,
    },
  };

  const assignee = principalFromOwner(prd.owner);
  if (assignee) contract.assigned_to = assignee;

  contract.risk_tier = options.riskTier;
  contract.scope = buildScope(prd.manifest, options.repository);
  contract.context = prd.sourceDocuments.map((reference) => ({
    id: `ctx:${idSegment(reference.replace(/\.[A-Za-z0-9]+$/, ''))}`,
    version: 'unpinned',
    uri: reference,
  }));
  contract.capabilities = buildCapabilities(prd);
  contract.acceptance = buildAcceptance(prd.acceptance, prd.gateText);
  contract.constraints = { external_effects_allowed: false, max_retries: 1 };
  contract.dependencies = sortedSet(
    prd.dependsOn.map((entry) => `workstream:${idSegment(entry.toLowerCase())}`)
  );
  if (prd.nonGoals.length > 0) contract.non_goals = prd.nonGoals;

  return contract;
}

// --- cli --------------------------------------------------------------------

function parseArgv(argv) {
  const inputs = [];
  const options = {
    out: null,
    riskTier: DEFAULTS.riskTier,
    repository: DEFAULTS.repository,
    requestedBy: DEFAULTS.requestedBy,
    requestedByName: DEFAULTS.requestedByName,
    contractVersion: DEFAULTS.contractVersion,
    schemaVersion: DEFAULTS.schemaVersion,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--out':
        options.out = argv[++index];
        break;
      case '--risk-tier':
        options.riskTier = argv[++index];
        break;
      case '--repository':
        options.repository = argv[++index];
        break;
      case '--requested-by':
        options.requestedBy = argv[++index];
        break;
      case '--requested-by-name':
        options.requestedByName = argv[++index];
        break;
      case '--contract-version':
        options.contractVersion = argv[++index];
        break;
      case '--schema-version':
        options.schemaVersion = argv[++index];
        break;
      case '-h':
      case '--help':
        options.help = true;
        break;
      default:
        if (arg.startsWith('--')) throw new Error(`unknown flag: ${arg}`);
        inputs.push(arg);
    }
  }
  return { inputs, options };
}

const USAGE = [
  'Usage: node prd-to-contract.cjs <prd.md> [<prd.md> ...] --out <dir>',
  '',
  '  --out <dir>             output directory (required)',
  `  --risk-tier <R0..R4>    default ${DEFAULTS.riskTier}`,
  `  --repository <id>       repository id for every scope entry, default ${DEFAULTS.repository}`,
  `  --requested-by <id>     default ${DEFAULTS.requestedBy}`,
  '  --requested-by-name <s> display name for the requester',
  `  --contract-version <v>  default ${DEFAULTS.contractVersion}`,
  `  --schema-version <v>    default ${DEFAULTS.schemaVersion}`,
].join('\n');

function main() {
  let parsed;
  try {
    parsed = parseArgv(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    console.error(USAGE);
    process.exit(2);
  }
  const { inputs, options } = parsed;

  if (options.help) {
    console.log(USAGE);
    return;
  }
  if (inputs.length === 0 || !options.out) {
    console.error(USAGE);
    process.exit(2);
  }

  fs.mkdirSync(options.out, { recursive: true });

  for (const input of inputs) {
    const prdPath = path.resolve(input);
    const jobSlug = slug(path.basename(path.dirname(prdPath))) || slug(path.basename(prdPath, '.md'));
    const prd = parsePrd(prdPath);

    const problems = [];
    if (prd.title === '') problems.push('no "# PRD — <name>" heading');
    if (prd.outcome === '') problems.push('empty Feature Overview paragraph');
    if (prd.acceptance.length === 0) problems.push('no "- [ ]" acceptance criteria');
    if (prd.manifest.read.length + prd.manifest.write.length === 0) {
      problems.push('no paths in the read/write file manifest');
    }
    if (problems.length > 0) {
      console.error(`${input}: cannot derive a work contract — ${problems.join('; ')}`);
      process.exit(1);
    }

    const contract = buildContract(prd, jobSlug, options);
    const outPath = path.join(options.out, `${jobSlug}.json`);
    fs.writeFileSync(outPath, `${JSON.stringify(contract, null, 2)}\n`, 'utf8');
    console.log(`${input} -> ${outPath}`);
  }

  // Reported, never stored: keeping the run time out of the document is what
  // makes a regenerated contract byte-identical to its committed copy.
  console.error(`Generated ${inputs.length} contract(s) at ${new Date().toISOString()}.`);
}

main();
