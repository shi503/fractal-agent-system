# FRACTAL contracts

Runtime-neutral JSON Schema (draft-07) contracts for FRACTAL work — a typed
layer describing the same handful of concepts the markdown PRD/HANDOFF flow
already carries in prose: a unit of requested work, the runtime evidence it
produces, the events emitted while it runs, and the terminal handoff.

## What is here

| File | Describes |
|---|---|
| `schemas/common.schema.json` | Shared types: `id`, `version`, `timestamp`, `sha256`, `risk_tier`, `classification`, `principal`, `resource_ref`. No root instance type — it exists to be `$ref`'d by the other seven. |
| `schemas/repository.schema.json` | A registered repository: identity, owners, interfaces, deterministic checks. |
| `schemas/context-artifact.schema.json` | A piece of shared context: ownership, classification, freshness window, permitted principals, provenance. |
| `schemas/capability.schema.json` | A declared, vendor-neutral capability and its risk boundary. |
| `schemas/work-contract.schema.json` | A job/workstream: outcome, scope, context, required capabilities, acceptance criteria, constraints, dependencies. |
| `schemas/event.schema.json` | A CloudEvents-shaped lifecycle event (`fractal.work.*`) with FRACTAL correlation fields. |
| `schemas/evidence.schema.json` | Immutable evidence metadata: kind, producer, redaction, provenance. |
| `schemas/handoff.schema.json` | A terminal workstream result linked to its checks and evidence. |
| `scripts/validate-contracts.cjs` | Validates a directory of example instances against these schemas. Stdlib Node only — no `ajv`, no `node_modules`. |
| `scripts/project-work-graph.cjs` | Spike: projects a declared/observed work graph from a coherent contract bundle. |
| `scripts/resolve-context-bundle.cjs` | Spike: resolves a permission/version/hash/freshness-checked context bundle for a work contract. |
| `examples/*.json` | One minimal valid instance per instantiable schema (7 files — `common` has no instance of its own). |
| `examples/invalid/` | A deliberately invalid instance (`work-contract` missing its required `outcome`), kept here as a fixture and never passed to the default validation run. |
| `examples/fixtures/graph-demo-bundle.json` | A single coherent bundle (repository + context artifact + capability + work contract + two events + evidence + handoff) that the two spike scripts read. |

All example and fixture data uses the repo's TaskFlow/NOVA fixture
vocabulary (`repo:taskflow`, initiative NOVA, `WS-1`/`notification-schema`,
cast `person:AR`) — see `fixtures/taskflow/README.md` for the fiction this
draws from. Nothing here is derived from a real system, org, or person.

## Running the validator

```bash
node tools/contracts/scripts/validate-contracts.cjs tools/contracts/examples
node tools/contracts/scripts/validate-contracts.cjs tools/contracts/examples/invalid   # expect non-zero exit
node tools/contracts/scripts/project-work-graph.cjs
node tools/contracts/scripts/resolve-context-bundle.cjs
```

Each example file is a JSON object with a top-level `"$schemaRef"` string
(e.g. `"work-contract"`) naming which schema in `schemas/` it validates
against; the key is stripped before validation. `validate-contracts.cjs`
scans every `*.json` file directly inside the directory it is given — it
does not recurse, so pointing it at `examples/` never picks up
`examples/invalid/` or `examples/fixtures/` by accident.

The validator implements the draft-07 subset these eight schemas actually
use (`type`, `enum`, `const`, `pattern`, `format` for `date-time`/`uri`/
`uri-reference`, length/item/numeric bounds, `properties`,
`additionalProperties`, `required`, and same-document plus cross-file
`$ref`). It is not a general-purpose JSON Schema validator — it does not
implement `oneOf`/`anyOf`/`allOf`, `if`/`then`/`else`, or remote `$ref`
resolution, none of which these schemas use.

## Relationship to the markdown PRD/HANDOFF flow

**This does not replace the markdown FRACTAL flow.** A workstream PRD, its
PULSE entries, and its HANDOFF.md remain the actual artifacts a Feature Lead
reads and writes; nothing in the router, the skills, or the agent
instructions reads or writes these schemas today. The contracts are a typed
description of the same shapes — useful as a target for anyone who later
wants to emit or validate that data as JSON (a dashboard, a CI gate, a
non-Claude runtime), not a mechanism the harness currently exercises.

Rough correspondence, for orientation:

| Markdown artifact | Nearest schema |
|---|---|
| Workstream PRD (goal, scope, acceptance criteria) | `work-contract.schema.json` |
| PULSE heartbeat | `event.schema.json` |
| Build/test/lint gate output | `evidence.schema.json` |
| HANDOFF.md | `handoff.schema.json` |

The correspondence is illustrative, not a mapping any code enforces — a PRD
is prose written for a human/agent reader; a work-contract instance is
data written for a validator. Wiring the two together (e.g. generating a
work-contract from a PRD's frontmatter, or a handoff instance from a
HANDOFF.md) is out of scope here and not attempted.

## What is not wired up

- No part of the router, PULSE, or HANDOFF tooling reads or writes these
  schemas.
- No CI gate in this repository runs `validate-contracts.cjs` today.
- The two spike scripts (`project-work-graph.cjs`,
  `resolve-context-bundle.cjs`) are illustrations of what a consumer could
  do with a coherent contract bundle, not services anything depends on.

## Versioning

Schema versions use semantic versions. Additive optional fields may
increment the minor version. New required fields or changed meanings
require a major version and a migration plan. Events and stored artifacts
retain the version they were validated against.
