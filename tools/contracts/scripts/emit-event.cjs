#!/usr/bin/env node
// emit-event.cjs — append one schema-valid FRACTAL work event to a JSON
// Lines log. Stdlib Node only, no node_modules.
//
// Usage:
//   node emit-event.cjs --workstream-id <id> --router-status <status> [options]
//   node emit-event.cjs --workstream-id <id> --type <event-type> --status <status> [options]
//
// Call pattern: the orchestration loop invokes this alongside every
// `router.py update <workstream> <status>` call — one event per state
// transition, appended before or after the router call in either order.
// `--router-status` is a convenience that maps a router status straight to
// an event type/status pair; pass `--type`/`--status` directly for finer
// control (e.g. a mid-flight `fractal.work.blocked`).
//
//   NOT_STARTED -> fractal.work.accepted   / accepted
//   IN_PROGRESS -> fractal.work.started    / running
//   COMPLETE    -> fractal.work.completed  / completed
//
// Each appended line is a standalone JSON object conforming to
// schemas/event.schema.json. This script does not validate its own output —
// feed the log to validate-contracts.cjs (one JSON file per line, each
// tagged "$schemaRef": "event") to gate it. See e2e-demo.sh for the pattern.
//
// Options:
//   --workstream-id <id>     required, e.g. workstream:notification-schema
//   --router-status <s>      NOT_STARTED | IN_PROGRESS | COMPLETE (sets type + status)
//   --type <event-type>      explicit event type (overrides --router-status default)
//   --status <status>        explicit status (overrides --router-status default)
//   --job-id <id>            default: job:<workstream slug>
//   --trace-id <id>          default: trace:<workstream slug>
//   --id <id>                default: event:<uuid>
//   --source <uri-ref>       default: urn:fractal:feature-lead
//   --subject <id>           default: same as --workstream-id
//   --actor-id <id>          default: agent:feature-lead
//   --actor-type <t>         human | agent | workload | service (default agent)
//   --actor-name <s>
//   --parent-event-id <id>
//   --policy-decision-id <id>
//   --capability-id <id>
//   --target <s>
//   --duration-ms <int>
//   --cost-usd <num>
//   --evidence-ref <id>      repeatable
//   --error-class <s>
//   --message <s>
//   --time <timestamp>       default: now (ISO 8601 UTC)
//   --schema-version <v>     default 1.0.0
//   --log <path>             default .claude/fractal/events.jsonl (relative to cwd)

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DEFAULTS = {
  schemaVersion: '1.0.0',
  source: 'urn:fractal:feature-lead',
  actorId: 'agent:feature-lead',
  actorType: 'agent',
  log: path.join('.claude', 'fractal', 'events.jsonl'),
};

const ROUTER_STATUS_MAP = {
  NOT_STARTED: { type: 'fractal.work.accepted', status: 'accepted' },
  IN_PROGRESS: { type: 'fractal.work.started', status: 'running' },
  COMPLETE: { type: 'fractal.work.completed', status: 'completed' },
};

function idSlug(id) {
  const value = String(id).includes(':') ? String(id).split(':').slice(1).join(':') : String(id);
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'workstream';
}

function parseArgv(argv) {
  const options = {
    schemaVersion: DEFAULTS.schemaVersion,
    source: DEFAULTS.source,
    actorId: DEFAULTS.actorId,
    actorType: DEFAULTS.actorType,
    log: DEFAULTS.log,
    evidenceRefs: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    switch (arg) {
      case '--workstream-id': options.workstreamId = next(); break;
      case '--router-status': options.routerStatus = next(); break;
      case '--type': options.type = next(); break;
      case '--status': options.status = next(); break;
      case '--job-id': options.jobId = next(); break;
      case '--trace-id': options.traceId = next(); break;
      case '--id': options.id = next(); break;
      case '--source': options.source = next(); break;
      case '--subject': options.subject = next(); break;
      case '--actor-id': options.actorId = next(); break;
      case '--actor-type': options.actorType = next(); break;
      case '--actor-name': options.actorName = next(); break;
      case '--parent-event-id': options.parentEventId = next(); break;
      case '--policy-decision-id': options.policyDecisionId = next(); break;
      case '--capability-id': options.capabilityId = next(); break;
      case '--target': options.target = next(); break;
      case '--duration-ms': options.durationMs = next(); break;
      case '--cost-usd': options.costUsd = next(); break;
      case '--evidence-ref': options.evidenceRefs.push(next()); break;
      case '--error-class': options.errorClass = next(); break;
      case '--message': options.message = next(); break;
      case '--time': options.time = next(); break;
      case '--schema-version': options.schemaVersion = next(); break;
      case '--log': options.log = next(); break;
      case '-h':
      case '--help': options.help = true; break;
      default:
        throw new Error(`unknown flag: ${arg}`);
    }
  }
  return options;
}

const USAGE = [
  'Usage: node emit-event.cjs --workstream-id <id> --router-status <NOT_STARTED|IN_PROGRESS|COMPLETE> [options]',
  '   or: node emit-event.cjs --workstream-id <id> --type <event-type> --status <status> [options]',
  '',
  'See the file header for the full option list and the router-status -> event-type/status map.',
].join('\n');

function buildEvent(options) {
  if (!options.workstreamId) throw new Error('--workstream-id is required');

  let type = options.type;
  let status = options.status;
  if (options.routerStatus) {
    const mapped = ROUTER_STATUS_MAP[options.routerStatus];
    if (!mapped) {
      throw new Error(`--router-status must be one of ${Object.keys(ROUTER_STATUS_MAP).join(', ')}`);
    }
    type = type || mapped.type;
    status = status || mapped.status;
  }
  if (!type) throw new Error('--type is required (or pass --router-status)');
  if (!status) throw new Error('--status is required (or pass --router-status)');

  const slug = idSlug(options.workstreamId);
  const jobId = options.jobId || `job:${slug}`;
  const traceId = options.traceId || `trace:${slug}`;
  const id = options.id || `event:${crypto.randomUUID()}`;
  const time = options.time || new Date().toISOString();

  const data = {
    schema_version: options.schemaVersion,
    job_id: jobId,
    workstream_id: options.workstreamId,
    trace_id: traceId,
    actor: {
      principal_id: options.actorId,
      principal_type: options.actorType,
    },
    status,
  };
  if (options.actorName) data.actor.display_name = options.actorName;
  if (options.parentEventId) data.parent_event_id = options.parentEventId;
  if (options.policyDecisionId) data.policy_decision_id = options.policyDecisionId;
  if (options.capabilityId) data.capability_id = options.capabilityId;
  if (options.target) data.target = options.target;
  if (options.durationMs !== undefined) data.duration_ms = Number(options.durationMs);
  if (options.costUsd !== undefined) data.cost_usd = Number(options.costUsd);
  if (options.evidenceRefs.length > 0) data.evidence_refs = options.evidenceRefs;
  if (options.errorClass) data.error_class = options.errorClass;
  if (options.message) data.message = options.message;

  return {
    specversion: '1.0',
    id,
    source: options.source,
    type,
    time,
    subject: options.subject || options.workstreamId,
    datacontenttype: 'application/json',
    data,
  };
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

  let event;
  try {
    event = buildEvent(options);
  } catch (error) {
    console.error(error.message);
    console.error(USAGE);
    process.exit(2);
  }

  const logPath = path.resolve(options.log);
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  fs.appendFileSync(logPath, `${JSON.stringify(event)}\n`, 'utf8');
  console.log(`${event.type} (${event.data.status}) -> ${logPath}`);
}

main();
