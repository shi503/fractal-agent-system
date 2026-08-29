paths: ["tools/decision-ledger/**", "fixtures/taskflow/decision-log/**"]
---

# Decision Ledger Protocol

**Canonical reference:** `tools/decision-ledger/schema/schema.yaml` (entry types, statuses,
RACI rules) and `tools/decision-ledger/README.md` (layout, CLI, testing).

## Markdown is canonical

Every entry is a plain `.md` file with YAML frontmatter under a decision-log directory (the
fixture: `fixtures/taskflow/decision-log/`). The SQLite index
(`tools/decision-ledger/storage/sqlite_index.py`) is a derived, disposable acceleration
structure — never edit it directly, and never treat it as the source of truth.

## Entry types and ID formats

Defined in `schema.yaml`'s `entry_types`; add a new type there, not in code (its own FM-5
guard comment: this is a YAML edit, never a change to the validator).

| Type | ID format | Use for |
|---|---|---|
| `discovery` | `D-NNNN` | Open questions or decision inputs |
| `critical_decision` | `CD-NNN` | Binary, high-impact decisions that gate progress |
| `big_idea` | `BI-NNN` | Strategic levers unlocking multiple items |
| `layer_item` | — | Layer-scoped items (see `schema.yaml` for its required fields) |

Every entry requires `id`, `type`, `title`, `owner`, `status`, `raci`, `created`, `updated`,
`created_by`, `updated_by`. `created_by` / `updated_by` and every RACI field must resolve
against a people registry (fixture: `fixtures/taskflow/people.yaml`).

## Status values

`open | in_discovery | answered | conflicted | pending_signoff | deferred` — an entry with
`status: open` or `in_discovery` is the equivalent of an open question; there is no separate
OQ-ID namespace. Use whichever entry type fits the content (usually `discovery`) and let
`status` carry the open/resolved distinction.

## Supersession

Superseded entries stay in the ledger. Set `superseded_by` to the ID of the entry that
replaces them rather than deleting or rewriting the old entry — the optional `superseded_by`
field exists on every entry type for exactly this.

## Validation

```bash
python3 tools/decision-ledger/schema/validate.py <directory-of-md-files>
```

Run this before treating any new or edited entry as ready. `tools/decision-ledger/storage/cli.py`
is the read/write CLI (`list`, `read <id>`, etc.); `tools/decision-ledger/safety/install.sh`
installs the optional multi-user pre-commit safety hook (locking, conflict preservation,
audit trail) — not installed by default.

## Rules

1. **Do not invent a new entry type ad hoc.** Extend `schema.yaml`'s `entry_types`; do not
   special-case a new shape in `validate.py` or the CLI.
2. **Conflicts between the ledger and execution reality** (a sibling repo, a shipped
   artifact) get surfaced explicitly, not silently reconciled — the ledger is wrong when it
   contradicts what actually happened, but that correction is itself a new or amended entry,
   not a quiet edit.
3. **State rules and decisions in the entry itself.** Reference an entry by its ID
   (`D-0001`, `CD-003`, …); do not re-litigate a locked, non-open-status entry without the
   entry's own owner reopening it.

<!-- referenced-paths
tools/decision-ledger/schema/schema.yaml
tools/decision-ledger/README.md
tools/decision-ledger/storage/sqlite_index.py
tools/decision-ledger/storage/cli.py
tools/decision-ledger/schema/validate.py
tools/decision-ledger/safety/install.sh
fixtures/taskflow/decision-log
fixtures/taskflow/people.yaml
-->
