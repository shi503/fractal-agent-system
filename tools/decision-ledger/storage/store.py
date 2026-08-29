"""
Decision Ledger v2 — Storage Layer Public API

This is the single entry point for all storage operations. Higher layers
(skill, sync daemon, MCP server) import only from this module.

Markdown is canonical. SQLite (.index.sqlite) is a derived index.
Deleting the index and calling rebuild_index() is fully lossless.

Configurable store root — default: projects/<project>/decision-log/
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add storage dir to sys.path so sibling imports work when called via CLI
_STORAGE_DIR = Path(__file__).parent
if str(_STORAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_STORAGE_DIR))

# Add schema dir to sys.path for validate.py access
_SCHEMA_DIR = _STORAGE_DIR.parent / "schema"
if str(_SCHEMA_DIR) not in sys.path:
    sys.path.insert(0, str(_SCHEMA_DIR))

from atomic_write import atomic_write, file_hash  # noqa: E402
from frontmatter import parse_frontmatter, render_entry  # noqa: E402
from sqlite_index import DecisionIndex  # noqa: E402


# ---------------------------------------------------------------------------
# Store class
# ---------------------------------------------------------------------------

class DecisionStore:
    """
    Markdown-canonical decision-ledger store.

    Typical usage:
        store = DecisionStore(Path("projects/<project>/decision-log"))
        entry = store.read("D-9001")
        store.write("D-9001", updated_frontmatter, body, actor="AR")
        store.rebuild_index()
        drift = store.verify_consistency()
    """

    INDEX_FILENAME = ".index.sqlite"
    PEOPLE_FILENAME = "people.yaml"

    def __init__(self, store_root: Path) -> None:
        self._root = store_root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        db_path = self._root / self.INDEX_FILENAME
        self._index = DecisionIndex(db_path)

    @property
    def root(self) -> Path:
        return self._root

    def close(self) -> None:
        self._index.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _entry_path(self, entry_id: str) -> Path:
        return self._root / f"{entry_id}.md"

    def _parse_file(self, path: Path) -> tuple[dict[str, Any], str, list[str]]:
        """Parse a .md file into (frontmatter, body, errors)."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return {}, "", [f"cannot read: {exc}"]
        return parse_frontmatter(text)

    # ------------------------------------------------------------------
    # read(id) → (frontmatter, body) | raises FileNotFoundError
    # ------------------------------------------------------------------

    def read(self, entry_id: str) -> tuple[dict[str, Any], str]:
        """
        Read an entry from the canonical markdown file.

        Returns (frontmatter_dict, body_text).
        Raises FileNotFoundError if the entry doesn't exist.
        """
        path = self._entry_path(entry_id)
        if not path.exists():
            raise FileNotFoundError(f"Entry not found: {entry_id} (expected {path})")
        fm, body, errors = self._parse_file(path)
        if errors:
            raise ValueError(f"Parse errors in {path.name}: {errors}")
        return fm, body

    # ------------------------------------------------------------------
    # write(id, frontmatter, body, actor) — atomic file + index update
    # ------------------------------------------------------------------

    def write(
        self,
        entry_id: str,
        frontmatter: dict[str, Any],
        body: str,
        actor: str,
    ) -> str:
        """
        Atomically write an entry.

        Steps:
          1. Check for a conflicting lock (held by a different actor).
          2. Render frontmatter + body to a markdown string.
          3. Capture before_hash of the existing file ('' if new).
          4. Write via temp-file + atomic rename.
          5. Update the SQLite index in a transaction.

        Returns the SHA-256 hash of the written content.

        Raises:
          PermissionError — if the entry is locked by a different actor.
          ValueError — if frontmatter is missing required 'id' field.
        """
        if frontmatter.get("id") != entry_id:
            frontmatter = {**frontmatter, "id": entry_id}

        self._check_lock(entry_id, actor)

        path = self._entry_path(entry_id)
        before_hash = file_hash(path)

        content = render_entry(frontmatter, body)
        after_hash = atomic_write(path, content)

        # Index update — runs immediately after successful file write.
        # If this fails, we have a markdown file with no index row (drift),
        # which verify_consistency() will detect and rebuild() will repair.
        self._index.upsert_entry(
            frontmatter,
            f"{entry_id}.md",
            after_hash,
            actor,
            before_hash,
        )

        return after_hash

    # ------------------------------------------------------------------
    # list(filters) → list of frontmatter dicts
    # ------------------------------------------------------------------

    def list_entries(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        List entries from the index (fast path).

        *filters* is a dict of field → value pairs for exact matches.
        Returns a list of frontmatter dicts ordered by entry ID.
        """
        return self._index.list_entries(filters)

    # ------------------------------------------------------------------
    # query(sql) → list of raw row dicts
    # ------------------------------------------------------------------

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """
        Execute arbitrary read-only SQL against the index.
        Only SELECT statements are accepted.
        """
        return self._index.query_raw(sql, params)

    # ------------------------------------------------------------------
    # lock / unlock (multi-user safety foundation)
    # ------------------------------------------------------------------

    def lock(self, entry_id: str, actor: str) -> bool:
        """
        Attempt to acquire a 5-minute lock on *entry_id* for *actor*.

        Returns True if acquired, False if held by a different actor.
        """
        return self._index.acquire_lock(entry_id, actor)

    def unlock(self, entry_id: str, actor: str) -> bool:
        """
        Release a lock on *entry_id*.

        Returns True if released, False if held by a different actor.
        """
        return self._index.release_lock(entry_id, actor)

    def get_lock(self, entry_id: str) -> dict[str, Any] | None:
        """Return the current lock record, or None if no lock is held."""
        return self._index.get_lock(entry_id)

    def renew_lock(self, entry_id: str, actor: str, ttl_seconds: int = 300) -> bool:
        """
        Renew (extend) an existing lock held by *actor* for another *ttl_seconds*.

        Long editing sessions must not lose their lock mid-flight due to TTL expiry.

        Returns True if renewed, False if the lock is not held by *actor* or doesn't exist.
        """
        return self._index.renew_lock(entry_id, actor, ttl_seconds)

    def list_active_locks(self) -> list[dict[str, Any]]:
        """Return all non-expired lock rows for 'who is editing what' visibility."""
        return self._index.list_active_locks()

    # ------------------------------------------------------------------
    # rebuild_index() — lossless full reconstruction
    # ------------------------------------------------------------------

    def rebuild_index(self, actor: str = "SYSTEM") -> dict[str, int]:
        """
        Walk the store root and rebuild .index.sqlite from scratch.

        Lossless: deleting the index file and calling rebuild_index() returns
        the same data as before. The markdown files are the source of truth.

        Returns stats: {parsed, upserted, skipped, deleted}.
        """
        return self._index.rebuild(
            self._root,
            parse_fn=self._parse_file,
            hash_fn=file_hash,
            actor=actor,
        )

    # ------------------------------------------------------------------
    # verify_consistency() — FM-1 guard
    # ------------------------------------------------------------------

    def verify_consistency(self) -> list[str]:
        """
        Compare the SQLite index against the markdown files on disk.

        Returns a list of drift messages. Empty list = clean (FM-1 satisfied).
        Implements the FM-1 guard: markdown and the derived index must never diverge.
        """
        return self._index.verify_consistency(
            self._root,
            parse_fn=self._parse_file,
            hash_fn=file_hash,
        )

    # ------------------------------------------------------------------
    # Internal: lock check before write
    # ------------------------------------------------------------------

    def _check_lock(self, entry_id: str, actor: str) -> None:
        """Raise PermissionError if *entry_id* is locked by a different actor."""
        lock = self._index.get_lock(entry_id)
        if not lock:
            return
        import time
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if lock["actor"] != actor and lock["expires_at"] > now_iso:
            raise PermissionError(
                f"Entry {entry_id} is locked by {lock['actor']} until {lock['expires_at']}. "
                f"Cannot write as {actor}."
            )
