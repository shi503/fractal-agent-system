"""
Decision Ledger v2 — SQLite Index

Derived index over markdown frontmatter fields. NEVER the source of truth.
Deleting this file and calling rebuildIndex() fully reconstructs it from markdown.

Tables:
  entries   — one row per decision entry; mirrors frontmatter fields
  locks     — optimistic-lock rows for multi-user safety
  audit_log — append-only write history

Driver: Python stdlib `sqlite3` (3.45.1 on dev workstations).
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entries (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    layer         TEXT,
    title         TEXT NOT NULL,
    owner         TEXT NOT NULL,
    status        TEXT NOT NULL,
    raci_json     TEXT NOT NULL,          -- JSON blob: {responsible, accountable, consulted, informed}
    options_json  TEXT,                   -- JSON array or NULL
    unlocks_json  TEXT,                   -- JSON array or NULL
    answer        TEXT,
    superseded_by TEXT,
    cross_refs_json TEXT,                 -- JSON array or NULL
    tags_json     TEXT,                   -- JSON array or NULL
    addenda_json  TEXT,                   -- JSON array or NULL
    created       TEXT NOT NULL,          -- ISO-8601
    updated       TEXT NOT NULL,          -- ISO-8601
    created_by    TEXT NOT NULL,
    updated_by    TEXT NOT NULL,
    body_hash     TEXT NOT NULL,          -- SHA-256 of full file content
    file_path     TEXT NOT NULL,          -- relative path within store root
    extra_json    TEXT                    -- unknown frontmatter fields preserved
);

CREATE INDEX IF NOT EXISTS idx_entries_type   ON entries(type);
CREATE INDEX IF NOT EXISTS idx_entries_status ON entries(status);
CREATE INDEX IF NOT EXISTS idx_entries_layer  ON entries(layer);
CREATE INDEX IF NOT EXISTS idx_entries_owner  ON entries(owner);

CREATE TABLE IF NOT EXISTS locks (
    id         TEXT PRIMARY KEY,          -- entry ID being locked
    actor      TEXT NOT NULL,             -- initials of lock holder
    acquired   TEXT NOT NULL,             -- ISO-8601
    expires_at TEXT NOT NULL,             -- ISO-8601  (acquired + 5 min)
    session_id TEXT                       -- opaque identifier for the editing session
);

CREATE TABLE IF NOT EXISTS audit_log (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id    TEXT NOT NULL,
    actor       TEXT NOT NULL,
    operation   TEXT NOT NULL,            -- 'write' | 'delete' | 'lock' | 'unlock' | 'rebuild'
    before_hash TEXT NOT NULL,            -- '' for new entries
    after_hash  TEXT NOT NULL,            -- '' for deletes
    timestamp   TEXT NOT NULL             -- ISO-8601
);
-- audit_log is insert-only; no UPDATE or DELETE is ever issued on it
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LIST_FIELDS = {"options", "unlocks", "cross_refs", "tags", "addenda"}
_JSON_COLS: dict[str, str] = {
    "raci": "raci_json",
    "options": "options_json",
    "unlocks": "unlocks_json",
    "cross_refs": "cross_refs_json",
    "tags": "tags_json",
    "addenda": "addenda_json",
}
_KNOWN_COLS = {
    "id", "type", "layer", "title", "owner", "status",
    "raci", "options", "unlocks", "answer", "superseded_by",
    "cross_refs", "tags", "addenda",
    "created", "updated", "created_by", "updated_by",
}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _fm_to_row(fm: dict[str, Any], file_path: str, body_hash: str) -> dict[str, Any]:
    """Convert a frontmatter dict to a SQLite row dict."""
    extra: dict[str, Any] = {}
    row: dict[str, Any] = {
        "id": fm["id"],
        "type": fm["type"],
        "layer": fm.get("layer"),
        "title": fm["title"],
        "owner": fm["owner"],
        "status": fm["status"],
        "raci_json": json.dumps(fm.get("raci") or {}),
        "options_json": json.dumps(fm["options"]) if "options" in fm else None,
        "unlocks_json": json.dumps(fm["unlocks"]) if "unlocks" in fm else None,
        "answer": fm.get("answer"),
        "superseded_by": fm.get("superseded_by"),
        "cross_refs_json": json.dumps(fm["cross_refs"]) if "cross_refs" in fm else None,
        "tags_json": json.dumps(fm["tags"]) if "tags" in fm else None,
        "addenda_json": json.dumps(fm["addenda"]) if "addenda" in fm else None,
        "created": fm["created"],
        "updated": fm["updated"],
        "created_by": fm["created_by"],
        "updated_by": fm["updated_by"],
        "body_hash": body_hash,
        "file_path": file_path,
    }
    for k, v in fm.items():
        if k not in _KNOWN_COLS:
            extra[k] = v
    row["extra_json"] = json.dumps(extra) if extra else None
    return row


def _row_to_fm(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row back to a frontmatter dict."""
    d = dict(row)
    fm: dict[str, Any] = {
        "id": d["id"],
        "type": d["type"],
        "title": d["title"],
        "owner": d["owner"],
        "status": d["status"],
        "raci": json.loads(d["raci_json"]) if d["raci_json"] else {},
        "created": d["created"],
        "updated": d["updated"],
        "created_by": d["created_by"],
        "updated_by": d["updated_by"],
    }
    if d.get("layer"):
        fm["layer"] = d["layer"]
    for fm_key, col in [
        ("options", "options_json"),
        ("unlocks", "unlocks_json"),
        ("cross_refs", "cross_refs_json"),
        ("tags", "tags_json"),
        ("addenda", "addenda_json"),
    ]:
        if d.get(col):
            fm[fm_key] = json.loads(d[col])
    if d.get("answer"):
        fm["answer"] = d["answer"]
    if d.get("superseded_by"):
        fm["superseded_by"] = d["superseded_by"]
    if d.get("extra_json"):
        extra = json.loads(d["extra_json"])
        fm.update(extra)
    return fm


# ---------------------------------------------------------------------------
# Index class
# ---------------------------------------------------------------------------

class DecisionIndex:
    """
    Manages the SQLite derived index for a decision-log store.

    The index is a *derived* view. The constructor opens (or creates) the
    database but does NOT rebuild it; callers must explicitly call rebuild().
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._con = sqlite3.connect(str(db_path), check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._con.executescript(DDL)
        self._con.commit()

    def close(self) -> None:
        self._con.close()

    # ------------------------------------------------------------------
    # Upsert a single entry row (called from write path)
    # ------------------------------------------------------------------

    def upsert_entry(
        self,
        fm: dict[str, Any],
        file_path: str,
        body_hash: str,
        actor: str,
        before_hash: str,
    ) -> None:
        """
        Upsert the entry row and append an audit_log record — in one transaction.
        """
        row = _fm_to_row(fm, file_path, body_hash)
        cols = list(row.keys())
        placeholders = ", ".join(f":{c}" for c in cols)
        updates = ", ".join(f"{c} = :{c}" for c in cols if c != "id")
        sql = (
            f"INSERT INTO entries ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}"
        )
        now = _now_iso()
        with self._con:
            self._con.execute(sql, row)
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fm["id"], actor, "write", before_hash, body_hash, now),
            )

    # ------------------------------------------------------------------
    # Remove an entry row (used by rebuild — stale rows deleted first)
    # ------------------------------------------------------------------

    def delete_entry(self, entry_id: str, actor: str, before_hash: str) -> None:
        now = _now_iso()
        with self._con:
            self._con.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, actor, "delete", before_hash, "", now),
            )

    # ------------------------------------------------------------------
    # Rebuild from filesystem (FM-1 guard — full index reconstruction)
    # ------------------------------------------------------------------

    def rebuild(
        self,
        store_root: Path,
        parse_fn: Any,   # callable(path) -> (fm, body, errors)
        hash_fn: Any,    # callable(path) -> str
        actor: str = "SYSTEM",
    ) -> dict[str, int]:
        """
        Walk *store_root* and rebuild the entries table from scratch.

        Steps:
          1. Read all .md files; parse frontmatter.
          2. Delete rows no longer backed by a .md file.
          3. Upsert all valid rows.
          4. Log one 'rebuild' audit record.

        Returns {'parsed': N, 'upserted': N, 'skipped': N, 'deleted': N}.
        """
        md_files = sorted(store_root.glob("*.md"))
        parsed = 0
        upserted = 0
        skipped = 0

        file_ids: set[str] = set()

        for md_path in md_files:
            fm, _body, errors = parse_fn(md_path)
            if errors or not fm.get("id"):
                skipped += 1
                continue
            parsed += 1
            body_hash = hash_fn(md_path)
            rel_path = str(md_path.relative_to(store_root))

            # Fetch existing hash to populate before_hash in audit
            cur = self._con.execute(
                "SELECT body_hash FROM entries WHERE id = ?", (fm["id"],)
            )
            existing = cur.fetchone()
            before_hash = existing["body_hash"] if existing else ""

            self.upsert_entry(fm, rel_path, body_hash, actor, before_hash)
            upserted += 1
            file_ids.add(fm["id"])

        # Remove stale rows (entries no longer on disk)
        cur = self._con.execute("SELECT id, body_hash FROM entries")
        stale = [(row["id"], row["body_hash"]) for row in cur if row["id"] not in file_ids]
        deleted = 0
        for stale_id, stale_hash in stale:
            self.delete_entry(stale_id, actor, stale_hash)
            deleted += 1

        now = _now_iso()
        with self._con:
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("*", actor, "rebuild", "", "", now),
            )

        return {"parsed": parsed, "upserted": upserted, "skipped": skipped, "deleted": deleted}

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_entry(self, entry_id: str) -> dict[str, Any] | None:
        """Return frontmatter dict for *entry_id*, or None."""
        cur = self._con.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        return _row_to_fm(row) if row else None

    def list_entries(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List entries optionally filtered by scalar fields.

        *filters* is a dict of column → value pairs for exact matches.
        Supported filter keys: type, status, layer, owner, updated_by.
        """
        where_clauses: list[str] = []
        params: list[Any] = []

        allowed_filter_keys = {"type", "status", "layer", "owner", "updated_by", "created_by"}
        for key, val in (filters or {}).items():
            if key in allowed_filter_keys:
                where_clauses.append(f"{key} = ?")
                params.append(val)

        sql = "SELECT * FROM entries"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY id"

        cur = self._con.execute(sql, params)
        return [_row_to_fm(row) for row in cur]

    def query_raw(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """
        Execute arbitrary read-only SQL against the index.
        Raises ValueError if the statement is not a SELECT.
        """
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
            raise ValueError("query_raw only accepts SELECT statements")
        cur = self._con.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur]

    # ------------------------------------------------------------------
    # Lock primitives (FM-7 foundation — concurrent-write guard)
    # ------------------------------------------------------------------

    def acquire_lock(self, entry_id: str, actor: str, ttl_seconds: int = 300) -> bool:
        """
        Attempt to acquire a 5-minute lock on *entry_id* for *actor*.

        Returns True if the lock was acquired, False if held by a different actor
        and not yet expired.  If the lock is held by *actor* it is refreshed.
        """
        now = _now_iso()
        cur = self._con.execute("SELECT actor, expires_at FROM locks WHERE id = ?", (entry_id,))
        existing = cur.fetchone()

        if existing:
            held_by = existing["actor"]
            expires = existing["expires_at"]
            if held_by != actor and expires > now:
                return False
            # Expired or same actor — fall through to upsert

        import datetime
        acquired_dt = datetime.datetime.now(datetime.timezone.utc)
        expires_dt = acquired_dt + datetime.timedelta(seconds=ttl_seconds)
        acquired_iso = acquired_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        expires_iso = expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        with self._con:
            self._con.execute(
                "INSERT INTO locks (id, actor, acquired, expires_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET actor=excluded.actor, acquired=excluded.acquired, expires_at=excluded.expires_at",
                (entry_id, actor, acquired_iso, expires_iso),
            )
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, actor, "lock", "", "", now),
            )
        return True

    def release_lock(self, entry_id: str, actor: str) -> bool:
        """
        Release a lock on *entry_id*.

        Returns True if the lock was released, False if held by a different actor.
        """
        now = _now_iso()
        cur = self._con.execute("SELECT actor FROM locks WHERE id = ?", (entry_id,))
        existing = cur.fetchone()
        if not existing or existing["actor"] != actor:
            return False
        with self._con:
            self._con.execute("DELETE FROM locks WHERE id = ?", (entry_id,))
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, actor, "unlock", "", "", now),
            )
        return True

    def get_lock(self, entry_id: str) -> dict[str, Any] | None:
        """Return the current lock record for *entry_id*, or None."""
        cur = self._con.execute("SELECT * FROM locks WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def renew_lock(self, entry_id: str, actor: str, ttl_seconds: int = 300) -> bool:
        """
        Extend an existing lock held by *actor* for another *ttl_seconds*.

        Returns True if renewed, False if the lock is not held by *actor* or doesn't exist.

        Long editing sessions must not lose their lock mid-flight when the default
        5-minute TTL elapses.  Callers should renew before the TTL expires (e.g., every
        4 minutes).
        """
        now = _now_iso()
        cur = self._con.execute("SELECT actor, expires_at FROM locks WHERE id = ?", (entry_id,))
        existing = cur.fetchone()
        if not existing or existing["actor"] != actor:
            return False

        import datetime
        new_expires_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=ttl_seconds)
        new_expires_iso = new_expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        with self._con:
            self._con.execute(
                "UPDATE locks SET expires_at = ? WHERE id = ? AND actor = ?",
                (new_expires_iso, entry_id, actor),
            )
            self._con.execute(
                "INSERT INTO audit_log (entry_id, actor, operation, before_hash, after_hash, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, actor, "lock_renew", "", new_expires_iso, now),
            )
        return True

    def list_active_locks(self) -> list[dict[str, Any]]:
        """Return all non-expired lock rows ordered by acquisition time."""
        now = _now_iso()
        cur = self._con.execute(
            "SELECT id, actor, acquired, expires_at FROM locks WHERE expires_at > ? ORDER BY acquired",
            (now,),
        )
        return [dict(row) for row in cur]

    # ------------------------------------------------------------------
    # FM-1 Guard: consistency check
    # ------------------------------------------------------------------

    def verify_consistency(
        self,
        store_root: Path,
        parse_fn: Any,
        hash_fn: Any,
    ) -> list[str]:
        """
        Compare index ↔ markdown frontmatter for every entry in the index.

        Returns a list of drift messages. Empty list = clean.
        Implements the FM-1 guard: the SQLite index must never silently diverge
        from the markdown files on disk.
        """
        drift: list[str] = []
        cur = self._con.execute("SELECT * FROM entries ORDER BY id")
        rows = list(cur)

        indexed_ids: set[str] = set()
        for row in rows:
            entry_id = row["id"]
            indexed_ids.add(entry_id)
            idx_hash = row["body_hash"]
            file_path = store_root / row["file_path"]

            if not file_path.exists():
                drift.append(f"FM-1 DRIFT: {entry_id} — indexed but file not found: {file_path}")
                continue

            disk_hash = hash_fn(file_path)
            if disk_hash != idx_hash:
                drift.append(
                    f"FM-1 DRIFT: {entry_id} — hash mismatch "
                    f"(index={idx_hash[:12]}… disk={disk_hash[:12]}…)"
                )
                continue

            # Parse and compare key fields
            fm, _body, errors = parse_fn(file_path)
            if errors:
                drift.append(f"FM-1 DRIFT: {entry_id} — parse error on disk file: {errors[0]}")
                continue

            idx_fm = _row_to_fm(row)
            for field in ("status", "title", "owner", "updated"):
                idx_val = idx_fm.get(field)
                disk_val = fm.get(field)
                if idx_val != disk_val:
                    drift.append(
                        f"FM-1 DRIFT: {entry_id}.{field} — "
                        f"index={idx_val!r} disk={disk_val!r}"
                    )

        # Check for .md files NOT in the index
        for md_path in sorted(store_root.glob("*.md")):
            fm, _body, errors = parse_fn(md_path)
            if errors or not fm.get("id"):
                continue
            if fm["id"] not in indexed_ids:
                drift.append(f"FM-1 DRIFT: {fm['id']} — file on disk not in index: {md_path.name}")

        return drift
