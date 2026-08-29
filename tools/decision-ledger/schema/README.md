# Decision Ledger v2 — Schema

This directory contains all schema configuration and the validate CLI for Decision Ledger v2.

## Files

| File | Purpose |
|------|---------|
| `schema.yaml` | All entry types, status enum, layer enum, RACI constraints, field types |
| `people.yaml` | People registry: initials → name, role, default RACI, domain scopes |
| `schema-examples.md` | One fully-populated example per entry type (round-trip test corpus) |
| `test-fixtures/` | The same four examples as standalone `.md` files, used by the storage/safety test suites |
| `validate.py` | Standalone CLI: validates `.md` files against schema + people registry |

## How to validate entries

```bash
# Validate a directory of .md files:
python3 tools/decision-ledger/schema/validate.py path/to/decision-log/

# Validate a single file:
python3 tools/decision-ledger/schema/validate.py path/to/D-9001.md
```

Python 3.9+ required. No dependencies beyond stdlib.

## Why Python, not TypeScript?

The validate CLI uses only Python stdlib (no PyYAML, no pip install) so schema
validation never depends on whatever JS/TS toolchain the rest of a repo happens
to use. Python 3.12 is assumed available; the parser itself only needs 3.9+.
If a project later wants a Node-native validator (e.g., as a pre-commit hook via
`npm run validate`), add a thin wrapper script that shells out to
`python3 schema/validate.py`.

## FM-5 guard: adding a new entry type

**To add a new entry type (e.g., `RFC-NN`), edit `schema.yaml` only — no code changes.**

Steps:
1. Open `schema.yaml`.
2. Under `entry_types:`, add a new block following the existing pattern:
   ```yaml
   rfc:
     description: "Request for Comments. ID format: RFC-NN."
     id_pattern: "^RFC-[0-9]{1,2}$"
     id_label: "RFC-NN"
     required_fields:
       - id
       - type
       - title
       - owner
       - status
       - raci
       - created
       - updated
       - created_by
       - updated_by
     optional_fields:
       - layer
       - answer
       - cross_refs
       - tags
       - addenda
   ```
3. Add an example entry to `schema-examples.md`.
4. Run `validate.py` on the new example to confirm it passes.

The validate CLI reads `entry_types` at runtime — it enumerates types from `schema.yaml`,
not from any hard-coded list. No other changes are needed.

## Adding a new person

Edit `people.yaml` and add an entry under `people:`:

```yaml
  XX:
    name: "Full Name"
    role: "Role"
    allocation: "100%"
    default_raci: "R"
    domains:
      - L4
    notes: "Brief description."
```

Initials must be 2–4 uppercase letters. They are immediately usable in RACI fields
of any entry once `people.yaml` is saved.

To point the validator at a different registry (e.g. a project-specific one, rather
than editing this file in place), set `DL_PEOPLE_PATH` before running `validate.py`.

## Adding a new layer

Edit `schema.yaml` under both `layers:` and `allowed_layers:`:

```yaml
layers:
  L12:
    name: "Data Platform"
    description: "Data warehouse, analytics, ETL pipelines."

allowed_layers:
  - ...existing...
  - L12
```

## Schema decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Canonical format | Plain `.md` with YAML frontmatter | Human-readable, diffable, editable without tooling |
| SQLite | Derived index only | Never canonical; rebuilt from markdown on demand |
| Status strings | `open`, `in_discovery`, etc. | Emojis (🔴🟡) preserved in rendered views only |
| `responsible` min 1 | Enforced | FM-4 guard: every decision must have an owner |
| Initials resolve to `people.yaml` | Enforced | RACI referential integrity without a database |
| ISO-8601 timestamps | Required | Audit trail integrity — non-negotiable |
| Validator language | Python 3 stdlib | No external dependency; runs anywhere |
