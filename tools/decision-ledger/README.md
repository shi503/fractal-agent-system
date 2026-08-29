# Decision Ledger v2

A markdown-canonical, SQLite-derived decision log with schema-driven
validation and a multi-user safety layer (locking, conflict preservation,
audit trail). Every entry is a plain `.md` file with YAML frontmatter — the
SQLite index is a derived, disposable acceleration structure, never the
source of truth.

## Layout

```
tools/decision-ledger/
├── storage/         — markdown-canonical store, SQLite index, `dl` CLI
├── schema/           — entry-type definitions, people registry, validator
├── safety/            — multi-user locking, conflict resolution, pre-commit hook
├── import-pattern/    — v1-table import pattern + one worked example
└── tests/              — cross-cutting regression tests (see below)
```

Each subdirectory has its own README with the detail for that layer.
Start with `schema/README.md` if you're defining entry types, `storage/README.md`
for the storage API and CLI, `safety/README.md` for the locking/conflict model,
and `import-pattern/README.md` if you're importing an existing discovery log.

## Quick start

```bash
# Validate a directory of entries against schema.yaml + people.yaml
python3 tools/decision-ledger/schema/validate.py path/to/decision-log/

# Use the CLI
python3 tools/decision-ledger/storage/cli.py --store path/to/decision-log list
python3 tools/decision-ledger/storage/cli.py --store path/to/decision-log read D-9001

# Install the multi-user safety pre-commit hook (idempotent; not installed by default)
bash tools/decision-ledger/safety/install.sh
```

All tooling is Python 3.9+ stdlib only — no `pip install` required.

## Testing

```bash
python3 -m pytest tools/decision-ledger -q
```

Test suites, by directory:

| Directory | What it covers |
|-----------|-----------------|
| `storage/test_storage.py` | Atomic write, frontmatter round-trip, index rebuild, FM-1 drift detection, locks, audit log, CLI smoke tests |
| `schema/test_schema_examples.py` | Every documented schema example round-trips through the validator |
| `safety/test_multi_user_safety.py` | The four concurrent-write smoke tests, lock renewal, active-locks view, audit completeness |
| `import-pattern/test_import_pattern.py` | The generic v1-table helpers, plus an end-to-end run of the worked import example |
| `tests/test_macos_portability.py` | Regression test for the resolved-vs-unresolved-path bug in the pre-commit hook (see below) |
| `tests/test_malformed_entry_rejected.py` | The validator rejects a deliberately malformed entry (`tests/malformed/D-BAD.md`) |

## The macOS symlinked-tmpdir fix

`safety/pre_commit_hook.py`'s `run_hook()` used to compute
`store_root.relative_to(repo_root)` without resolving either path. Because
`storage/store.py`'s `DecisionStore` always `.resolve()`s its own root, and a
git-discovered repo root is not guaranteed to be pre-resolved, the two paths
could disagree on machines where the OS temp directory sits behind a symlink
(macOS's `/var` → `/private/var` is the common case) — the hook would raise
`ValueError` and crash on every commit. Both paths are now resolved before
the comparison. `tests/test_macos_portability.py` reproduces the divergence
with an explicit symlink (not dependent on any one OS's specific layout) and
fails without the fix, passes with it.

## What's synthetic in this port

`schema/people.yaml` and `schema/test-fixtures/` are a synthetic registry and
fixture corpus for this repository, distinct from `fixtures/taskflow/`'s own
decision-log fixtures — the two never share an ID. `import-pattern/` carries
the generic parts of a v1-table importer, demonstrated against
`fixtures/taskflow/v1-sample.md`; it is not a drop-in importer for any
particular project's discovery-log format (see `import-pattern/README.md`).
