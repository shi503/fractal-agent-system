# Decision Ledger v2 — Storage Layer

This directory implements the markdown-canonical storage layer for Decision Ledger v2.
It is the keystone layer; all higher layers (safety, importer, any future sync daemon)
import from here.

## Architecture invariant

**Markdown is canonical. SQLite is a derived index.**

```
tools/decision-ledger/
└── storage/
    ├── store.py          # Public API — the only import higher layers need
    ├── atomic_write.py   # Temp-file + atomic rename (POSIX rename(2))
    ├── frontmatter.py    # YAML frontmatter parser + serialiser (stdlib only)
    ├── sqlite_index.py   # SQLite derived index (DecisionIndex class)
    ├── write_adapter.py  # Scripted write helper: lock -> validate -> write -> lint -> unlock
    ├── cli.py            # `dl` CLI — manual ops
    ├── test_storage.py   # storage-layer test suite
    └── README.md         # This file
```

The default store root is:
```
tools/decision-ledger/decision-log/
```
or any path passed via `--store` / `DL_STORE`, e.g. `projects/<project>/decision-log/`.

Inside that directory:
```
<store-root>/
├── D-9001.md           ← canonical markdown entries (one file per entry)
├── CD-1.md
├── BI-1.md
├── L2-01a.md
├── .index.sqlite       ← DERIVED — delete and rebuild at any time
└── people.yaml         ← optional mirror of schema/people.yaml
```

## FM-1 Guard (canonical drift detection)

FM-1 is the risk that the SQLite index silently diverges from the markdown files.
Guards implemented in this layer:

1. **Single write path** — every entry write calls `DecisionStore.write()`, which
   atomically writes the markdown file and then updates the SQLite row in one transaction.
   There is no path that writes one without the other.

2. **`verify_consistency()`** — walks the index and compares every row against its
   markdown file by SHA-256 hash. Reports byte-level drift. Also catches:
   - Files indexed but no longer on disk
   - Files on disk not yet in the index

3. **`rebuild_index()`** — lossless full reconstruction. Deleting `.index.sqlite`
   and running `rebuild-index` returns identical data. The markdown files are the
   single source of truth.

Run the lint check at any time:
```bash
python3 tools/decision-ledger/storage/cli.py --store <decision-log-dir> verify
```

Expected output when clean:
```
FM-1 OK — index and markdown are consistent.
```

If drift is detected, the output lists each mismatch and exits with code 1.
The repair is always: `rebuild-index`.

## Public API

All higher layers import from `store.py`:

```python
from tools.decision_ledger.storage.store import DecisionStore

store = DecisionStore(Path("projects/<project>/decision-log"))

# Read a single entry
fm, body = store.read("D-9001")

# Write an entry (atomic: file + index in one transaction)
store.write("D-9001", fm, body, actor="AR")

# List with optional filters
entries = store.list_entries({"status": "open"})
entries = store.list_entries({"type": "discovery", "layer": "L4"})

# Raw SQL against the index (SELECT only)
rows = store.query("SELECT id, status FROM entries WHERE owner = ?", ("AR",))

# Lock primitives (multi-user safety)
store.lock("D-9001", "AR")     # → True if acquired, False if held by another actor
store.unlock("D-9001", "AR")   # → True if released

# FM-1 guard
drift = store.verify_consistency()  # → [] if clean

# Full index rebuild (lossless)
stats = store.rebuild_index()  # → {parsed, upserted, skipped, deleted}

store.close()
```

## CLI (`dl`)

```bash
# Set up: run from the repo root
alias dl="python3 tools/decision-ledger/storage/cli.py"

# Read an entry
dl read D-9001

# List all entries
dl list

# Filter by status / type / layer / owner
dl list --status open
dl list --type discovery --layer L4

# Rebuild the index from markdown
dl rebuild-index --actor AR

# FM-1 consistency check
dl verify

# Lock / unlock an entry (5-minute TTL)
dl lock D-9001 --actor AR
dl unlock D-9001 --actor AR

# Audit log
dl audit
dl audit --id D-9001
```

All commands accept `--store <path>` to override the default store root.

## Write path (atomicity guarantee)

Every `store.write()` call follows this sequence:

1. Check for a conflicting lock — raise `PermissionError` if held by another actor.
2. Capture `before_hash` of the existing file (empty string for new entries).
3. Render frontmatter + body to a markdown string.
4. Write to a temp file in the same directory (`os.replace()` is atomic on POSIX).
5. `fsync()` the temp file.
6. `os.replace(tmp, dest)` — atomic rename.
7. `DecisionIndex.upsert_entry()` — update the SQLite row + audit_log in one transaction.

If step 4–6 fails, the original file is untouched (the temp file is cleaned up).
If step 7 fails, the markdown file is updated but the index row is stale —
`verify_consistency()` will detect this; `rebuild_index()` repairs it.

## Lock primitives (multi-user safety foundation)

`locks` table in `.index.sqlite`:

| Column     | Type | Description                    |
|------------|------|--------------------------------|
| id         | TEXT | Entry ID (primary key)         |
| actor      | TEXT | Initials of lock holder        |
| acquired   | TEXT | ISO-8601 timestamp             |
| expires_at | TEXT | acquired + 5 minutes           |
| session_id | TEXT | Opaque session identifier      |

The `safety/` layer builds on this table. The seam for pre-commit hooks: any write
path (CLI, editor file-watcher, etc.) checks the `locks` table via
`DecisionStore.write()` before modifying the file.

## Audit log

`audit_log` table in `.index.sqlite` — insert-only:

| Column      | Type    | Description                              |
|-------------|---------|-------------------------------------------|
| rowid       | INTEGER | Auto-increment primary key               |
| entry_id    | TEXT    | Entry ID (`*` for rebuild operations)    |
| actor       | TEXT    | Initials of the person or system         |
| operation   | TEXT    | `write`, `delete`, `lock`, `unlock`, `rebuild` |
| before_hash | TEXT    | SHA-256 of file before write ('' = new)  |
| after_hash  | TEXT    | SHA-256 of file after write ('' = delete)|
| timestamp   | TEXT    | ISO-8601 UTC                             |

No UPDATE or DELETE is ever issued on `audit_log`. Every write produces a row.

## Driver choice: Python `sqlite3` (stdlib)

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **Python `sqlite3` (stdlib)** | **CHOSEN** | Zero dependencies; runs on any Python 3.9+ workstation; no JS/TS runtime entanglement; SQLite 3.45.1 supports WAL mode + foreign keys |
| An ORM (Drizzle, Prisma) | Rejected | Requires an npm/bun install and, for Prisma, a generate step + engine binary; designed for multi-environment DB migrations, not a local derived index; overkill for this use case |
| `node:sqlite` (Node stdlib) | Rejected | Still requires a Node/bun runtime; experimental API; no advantage over Python stdlib here |
| A native TS SQLite binding | Rejected | Fast and synchronous but still requires an npm/bun install for what is otherwise a single-user CLI tool |

Keeping the schema validator and the storage layer in the same language (Python
stdlib) means one runtime, one mental model, no cross-language impedance for the
CLI tool.

## Testing

```bash
python3 tools/decision-ledger/storage/test_storage.py
# or
python3 -m pytest tools/decision-ledger/storage/test_storage.py -v
```

Covers: atomic write, frontmatter round-trip (all 4 fixture types), index rebuild
losslessness, FM-1 drift detection (3 scenarios), lock conflict, audit log
completeness, query API, CLI smoke tests.
