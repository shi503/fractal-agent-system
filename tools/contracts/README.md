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
| `scripts/prd-to-contract.cjs` | Derives a `work-contract` instance from a template-conformant workstream PRD. Deterministic — see "Integration with the markdown FRACTAL flow" below. |
| `scripts/handoff-extract.cjs` | Extracts a `handoff` instance from a template-conformant `HANDOFF.md`. Deterministic — same section. |
| `scripts/project-work-graph.cjs` | Spike: projects a declared/observed work graph from a coherent contract bundle. |
| `scripts/resolve-context-bundle.cjs` | Spike: resolves a permission/version/hash/freshness-checked context bundle for a work contract. |
| `examples/*.json` | One minimal valid instance per instantiable schema (7 files — `common` has no instance of its own). |
| `examples/invalid/` | Deliberately invalid fixtures, never passed to the default validation run: `work-contract-missing-outcome.json` (a `work-contract` with no `outcome`), and `handoff-no-eval-table/HANDOFF.md` — a markdown HANDOFF that extracts to an invalid instance, the red case for the eval-template step. The subdirectory is invisible to the validator, which does not recurse. |
| `fixtures/taskflow/contracts/*.json` | The eight generated work contracts, one per fixture workstream. Regenerated from the PRDs, never hand-edited. |
| `examples/fixtures/graph-demo-bundle.json` | A single coherent bundle (repository + context artifact + capability + work contract + two events + evidence + handoff) that the two spike scripts read. |

All example and fixture data uses the repo's TaskFlow/NOVA fixture
vocabulary (`repo:taskflow`, initiative NOVA, `WS-1`/`notification-schema`,
cast `person:AR`) — see `fixtures/taskflow/README.md` for the fiction this
draws from. Nothing here is derived from a real system, org, or person.

## Running the validator

```bash
node tools/contracts/scripts/validate-contracts.cjs tools/contracts/examples
node tools/contracts/scripts/validate-contracts.cjs tools/contracts/examples/invalid   # expect non-zero exit
node tools/contracts/scripts/validate-contracts.cjs fixtures/taskflow/contracts
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

Two of those four rows now have code behind them — `prd-to-contract.cjs` for
the PRD row and `handoff-extract.cjs` for the HANDOFF row. The other two
(PULSE → event, gate output → evidence) remain correspondence only. The next
section documents exactly what the two scripts map and what they cannot.

## Integration with the markdown FRACTAL flow

The markdown artifacts stay the source of truth. A PRD is prose written for a
human or agent reader; a work-contract instance is data written for a
validator. The two scripts here derive the second from the first — a
projection, in one direction, that can be regenerated and thrown away. Nothing
writes back into a PRD or a HANDOFF, and no field lives only in the JSON.

### PRD → work contract

`prd-to-contract.cjs` reads the sections the PRD template already defines.

| PRD source | Contract field | Derivation |
|---|---|---|
| parent directory name | `job_id` | `job:<dir-slug>` — `.../workstreams/event-fanout/prd-event-fanout.md` → `job:event-fanout` |
| `**Workstream ID:**` | `workstream_id` | `workstream:` + the value lowercased (`WS-2` → `workstream:ws-2`) |
| `# PRD — <name>` heading | `title` | the name after the dash, verbatim |
| §1 first paragraph | `outcome` | the paragraph with backticks and bold markers stripped |
| §1 `**Source documents:**` | `context[]` | one `resource_ref` per entry: `id` = `ctx:<path minus extension>`, `uri` = the path, `version` = `"unpinned"` |
| §2 `- [ ]` criteria | `acceptance[]` | one entry each, in document order: `description` verbatim, `criterion_id` = `criterion:<slug of description, ≤60 chars>` |
| §3 `**Read only:**` | `scope[]` with `access: "read"` | paths de-duplicated and sorted |
| §3 `**Write / modify:**` + `**Create:**` | `scope[]` with `access: "write"` | both labels fold into the one write entry; paths de-duplicated and sorted |
| §4 CI-gate command block | `acceptance[].evidence_kinds` | pattern match over the commands → `build`, `typecheck`, `lint`, `test`, `e2e`, `migration`; `["review"]` when the block declares nothing |
| `**Model tier:**` | `capabilities[]` | `haiku` → `cap:mechanical-edit`, `sonnet` → `cap:scoped-implementation`, `opus` → `cap:design-authority` |
| presence of write paths | `capabilities[]` | always `cap:read-repository`; plus `cap:edit-isolated-repository` when the write scope is non-empty |
| `**Owner:** Feature Lead (XX)` | `assigned_to` | `person:XX`, `principal_type: "human"`; omitted when the owner carries no parenthetical |
| `**Depends on:**` | `dependencies[]` | `workstream:` + each entry lowercased, de-duplicated and sorted |
| §6 Out of Scope bullets | `non_goals[]` | one string per bullet, in document order |

Fields the PRD does not carry, supplied as documented defaults and overridable
by flag:

| Contract field | Default | Flag |
|---|---|---|
| `scope[].repository_id` | `repo:taskflow` | `--repository` |
| `requested_by` | `role:fractal-architect` / "FRACTAL Architect" | `--requested-by`, `--requested-by-name` |
| `risk_tier` | `R1` | `--risk-tier` |
| `schema_version`, `contract_version` | `1.0.0` | `--schema-version`, `--contract-version` |
| `constraints` | `{external_effects_allowed: false, max_retries: 1}` | — |

Regenerate the committed fixture contracts with:

```bash
node tools/contracts/scripts/prd-to-contract.cjs \
  fixtures/taskflow/workstreams/*/prd-*.md --out fixtures/taskflow/contracts
```

**Determinism.** The output carries no timestamp, hostname, or random id; keys
are written in one fixed order, set-like arrays are de-duplicated and sorted,
and inputs are consumed in argv order rather than by reading a directory. So
regenerating into a scratch directory and diffing against the committed copies
produces no differences at all, not merely differences confined to a generated
field:

```bash
OUT="$(mktemp -d)"
node tools/contracts/scripts/prd-to-contract.cjs \
  fixtures/taskflow/workstreams/*/prd-*.md --out "$OUT"
diff -r "$OUT" fixtures/taskflow/contracts   # expect empty
```

The generation time is printed to stderr instead of stored, which is what buys
the clean diff. Treat a non-empty diff as a real signal: either a PRD changed
or the generator did.

**What the derivation cannot do.** These are limits of the projection, not
bugs to file:

- `context[].version` is `"unpinned"` for every entry. A markdown PRD links a
  source document by path and nothing more — there is no version or content
  hash to read, so the contract cannot claim one. Pin them by hand, or from a
  registry, if a consumer ever needs freshness guarantees.
- `risk_tier` is a flat default. Risk is a judgment about blast radius that no
  amount of parsing recovers from prose; `R1` is a floor, and a human or the
  Architect sets the real tier.
- `requested_by` is a role, not a person. The PRD names its owner, never its
  requester.
- Every scope entry gets the same `repository_id`. A PRD lists paths and no
  repository, so a workstream that genuinely spans two repositories needs its
  scope split by hand after generation.
- `evidence_kinds` describes what the declared gate *would* produce, not what
  any run produced. Actual results belong in `evidence` and `handoff`.
- The generator refuses (exit 1) rather than guessing when a PRD has no title,
  no overview paragraph, no acceptance criteria, or an empty file manifest.

### HANDOFF → handoff instance

`handoff-extract.cjs` reads the sections the HANDOFF template defines.

| HANDOFF source | Instance field | Derivation |
|---|---|---|
| parent directory name | `handoff_id`, `job_id` | `handoff:<dir-slug>`, `job:<dir-slug>` |
| sibling `prd-*.md` → `**Workstream ID:**` | `workstream_id` | `workstream:ws-2`; falls back to the directory slug when no sibling PRD exists |
| `**Completed:**` | `created_at` | a bare `YYYY-MM-DD` becomes `YYYY-MM-DDT00:00:00Z`; anything else is passed through unchanged so the schema rejects it |
| §1 first bullet | `summary` | that bullet, emphasis stripped |
| §5 eval table rows | `checks[]` | `name` = first cell, `result` = second cell mapped `PASS`→`pass`, `FAIL`→`fail`, `N/A`/`skipped`→`not_run`; rows whose second cell is not a verdict (the header) are skipped |
| §5 eval table rows | `evidence_refs[]` | `evidence:<job-slug>-<slug of check name>`, de-duplicated and sorted |
| §5 results | `status` | `failed` if any row is `FAIL`, otherwise `accepted` |
| §2 bullets + §3 `**What:**` clauses | `limitations[]` | §2 contributes nothing when it reads `None`; §3 contributes the what-clause of each debt entry |
| §7 bullets | `next_actions[]` | one string per bullet |

Defaults: `produced_by` is `agent:feature-lead` / "FRACTAL Feature Lead"
(`--produced-by`, `--produced-by-name`); `schema_version` and
`contract_version` are `1.0.0`.

**What the extraction cannot do.**

- `status: "accepted"` is the Feature Lead's own claim that the gate passed,
  not an Architect verdict. `evaluated_by` stays empty because a HANDOFF is
  written before it is evaluated.
- `evidence_refs` are synthesized ids, not pointers to stored artifacts. They
  are stable and unique within one handoff; nothing resolves them yet.
- The extractor is lenient by design: it reports what the markdown carries and
  omits what it does not, so the schema — not a second parser with its own
  opinion — is the single definition of "structurally complete".

### Where this is used

`.claude/fractal/EVAL_TEMPLATES/deterministic-eval.md` §7 runs the HANDOFF
extraction and validation as a Layer-1 step. It is a structure gate: it
catches a HANDOFF that asserts completion while recording no gate evidence,
and it says nothing about whether a recorded **PASS** was real. That remains a
Layer-2 judgment.

## What is not wired up

- The router does not read or write these schemas. It reads blueprint YAML and
  writes workstream state, exactly as before; no contract file participates in
  advancing a workstream.
- The generated contracts under `fixtures/taskflow/contracts/` are validated
  artifacts, not inputs. Nothing consumes them — they exist so the derivation
  has committed output to diff against.
- Contract generation is not part of any gate. A PRD may change without its
  contract being regenerated, and nothing currently notices. Regenerate and
  diff if you want that guarantee.
- The HANDOFF step in the eval template is a documented manual command, not
  automation: no hook, watcher, or CI job invokes it.
- No CI gate in this repository runs `validate-contracts.cjs` today.
- The two spike scripts (`project-work-graph.cjs`,
  `resolve-context-bundle.cjs`) are illustrations of what a consumer could
  do with a coherent contract bundle, not services anything depends on.

## Versioning

Schema versions use semantic versions. Additive optional fields may
increment the minor version. New required fields or changed meanings
require a major version and a migration plan. Events and stored artifacts
retain the version they were validated against.
