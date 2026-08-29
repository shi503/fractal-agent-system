#!/usr/bin/env node
// handoff-extract.cjs — turn a template-conformant HANDOFF.md into a JSON
// instance of handoff.schema.json. Stdlib Node only, no node_modules.
//
// Usage:
//   node handoff-extract.cjs <HANDOFF.md> [<HANDOFF.md> ...] --out <dir> [options]
//
// Options:
//   --out <dir>              required; output directory (created if absent)
//   --produced-by <id>       default agent:feature-lead
//   --produced-by-name <s>   display name for the producer
//   --contract-version <v>   default 1.0.0
//   --schema-version <v>     default 1.0.0
//
// One JSON file per HANDOFF, named after its parent directory. Feed the
// output directory to validate-contracts.cjs; that is the actual gate.
//
// EXTRACT LENIENTLY, VALIDATE STRICTLY
// This script does not judge the HANDOFF. It reports what the markdown
// carries and omits what it does not, so a HANDOFF missing its eval table
// produces a document with no checks — and the schema, not this parser,
// is what rejects it. That split keeps one definition of "structurally
// complete" (the schema) instead of two.
//
// Like prd-to-contract.cjs this is deterministic: no timestamp, hostname,
// or random id reaches the output. `created_at` comes from the HANDOFF's
// own **Completed:** date.
//
// See tools/contracts/README.md, section "Integration with the markdown
// FRACTAL flow", for the section-by-section mapping and its known limits.

'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULTS = {
  schemaVersion: '1.0.0',
  contractVersion: '1.0.0',
  producedBy: 'agent:feature-lead',
  producedByName: 'FRACTAL Feature Lead',
};

// --- small text helpers -----------------------------------------------------

function stripEmphasis(text) {
  return text.replace(/`/g, '').replace(/\*\*/g, '').replace(/\s+/g, ' ').trim();
}

function slug(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function idSegment(text) {
  let out = text
    .replace(/[^A-Za-z0-9._~/-]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^[^A-Za-z0-9]+/, '')
    .replace(/[^A-Za-z0-9]+$/, '');
  if (out === '') out = 'unnamed';
  return out;
}

// --- markdown structure -----------------------------------------------------

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
    if (match) fields.set(match[1].trim().toLowerCase(), stripEmphasis(match[2]));
  }
  return fields;
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

function sectionIsNone(body) {
  for (const line of body) {
    const text = line.trim();
    if (text === '' || text.startsWith('>')) continue;
    return /^none\b/i.test(stripEmphasis(text));
  }
  return true;
}

function tableRows(body) {
  const rows = [];
  for (const line of body) {
    const text = line.trim();
    if (!text.startsWith('|')) continue;
    if (/^\|[\s|:-]*\|$/.test(text)) continue; // separator row
    const cells = text
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim());
    if (cells.length >= 2) rows.push(cells);
  }
  return rows;
}

const RESULT_WORDS = new Map([
  ['pass', 'pass'],
  ['passed', 'pass'],
  ['ok', 'pass'],
  ['fail', 'fail'],
  ['failed', 'fail'],
  ['n/a', 'not_run'],
  ['na', 'not_run'],
  ['not run', 'not_run'],
  ['not_run', 'not_run'],
  ['skipped', 'not_run'],
  ['skip', 'not_run'],
]);

function readResult(cell) {
  return RESULT_WORDS.get(stripEmphasis(cell).toLowerCase()) || null;
}

// --- extraction -------------------------------------------------------------

function siblingWorkstreamRef(handoffPath) {
  const dir = path.dirname(handoffPath);
  let entries;
  try {
    entries = fs.readdirSync(dir);
  } catch {
    return '';
  }
  const prd = entries
    .filter((name) => /^prd-.*\.md$/.test(name))
    .sort()[0];
  if (!prd) return '';
  const raw = fs.readFileSync(path.join(dir, prd), 'utf8');
  const fields = headerFields(raw.split('\n'));
  return fields.get('workstream id') || '';
}

function buildChecks(body, jobSlug) {
  const checks = [];
  const used = new Map();
  for (const cells of tableRows(body)) {
    const result = readResult(cells[1]);
    if (!result) continue; // header row, or a row that records no verdict
    const name = stripEmphasis(cells[0]);
    if (name === '') continue;
    const base = slug(name).slice(0, 60).replace(/-+$/, '') || 'check';
    const seen = (used.get(base) || 0) + 1;
    used.set(base, seen);
    const suffix = seen > 1 ? `-${seen}` : '';
    checks.push({
      name,
      result,
      evidence_id: `evidence:${idSegment(jobSlug)}-${base}${suffix}`,
    });
  }
  return checks;
}

function extract(handoffPath, options) {
  const raw = fs.readFileSync(handoffPath, 'utf8');
  const lines = raw.split('\n');
  const sections = splitSections(lines);
  const fields = headerFields(lines);

  const jobSlug = slug(path.basename(path.dirname(path.resolve(handoffPath)))) || 'handoff';
  const workstreamRef = siblingWorkstreamRef(path.resolve(handoffPath));

  const completedBody = findSection(sections, 'summary of work completed');
  const notCompletedBody = findSection(sections, 'summary of work not completed');
  const debtBody = findSection(sections, 'technical debt');
  const evalBody = findSection(sections, 'deterministic eval results');
  const nextBody = findSection(sections, 'next steps');

  const checks = buildChecks(evalBody, jobSlug);
  const summaryItems = bulletTexts(completedBody);

  const limitations = [];
  if (!sectionIsNone(notCompletedBody)) limitations.push(...bulletTexts(notCompletedBody));
  for (const line of debtBody) {
    const match = /^\s*(?:[-*]\s+)?\*\*What:\*\*\s*(.+)$/.exec(line);
    if (match) limitations.push(stripEmphasis(match[1]));
  }

  const document = {
    $schemaRef: 'handoff',
    schema_version: options.schemaVersion,
    handoff_id: `handoff:${idSegment(jobSlug)}`,
    job_id: `job:${idSegment(jobSlug)}`,
    workstream_id: `workstream:${idSegment((workstreamRef || jobSlug).toLowerCase())}`,
    contract_version: options.contractVersion,
    status: checks.some((check) => check.result === 'fail') ? 'failed' : 'accepted',
    produced_by: {
      principal_id: options.producedBy,
      principal_type: 'agent',
      display_name: options.producedByName,
    },
  };

  const completedOn = fields.get('completed');
  if (completedOn) {
    document.created_at = /^\d{4}-\d{2}-\d{2}$/.test(completedOn)
      ? `${completedOn}T00:00:00Z`
      : completedOn;
  }
  if (summaryItems.length > 0) document.summary = summaryItems[0];

  document.checks = checks;
  document.evidence_refs = Array.from(new Set(checks.map((check) => check.evidence_id))).sort();
  document.limitations = limitations;

  const nextActions = bulletTexts(nextBody);
  if (nextActions.length > 0) document.next_actions = nextActions;

  return { jobSlug, document };
}

// --- cli --------------------------------------------------------------------

function parseArgv(argv) {
  const inputs = [];
  const options = {
    out: null,
    producedBy: DEFAULTS.producedBy,
    producedByName: DEFAULTS.producedByName,
    contractVersion: DEFAULTS.contractVersion,
    schemaVersion: DEFAULTS.schemaVersion,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--out':
        options.out = argv[++index];
        break;
      case '--produced-by':
        options.producedBy = argv[++index];
        break;
      case '--produced-by-name':
        options.producedByName = argv[++index];
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
  'Usage: node handoff-extract.cjs <HANDOFF.md> [<HANDOFF.md> ...] --out <dir>',
  '',
  '  --out <dir>             output directory (required)',
  `  --produced-by <id>      default ${DEFAULTS.producedBy}`,
  '  --produced-by-name <s>  display name for the producer',
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
    const { jobSlug, document } = extract(input, options);
    const outPath = path.join(options.out, `${jobSlug}.json`);
    fs.writeFileSync(outPath, `${JSON.stringify(document, null, 2)}\n`, 'utf8');
    console.log(`${input} -> ${outPath}`);
  }
}

main();
