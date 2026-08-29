"""
Decision Ledger v2 — Conflict Resolver (FM-7 Guard)

When two writes race past the lock (e.g. the lock expired mid-edit), this module:
  1. Preserves the canonical file as-is
  2. Writes the competing version to <ID>.conflict-<actor>-<timestamp>.md
  3. Flips the canonical entry's status to "conflicted"
  4. Appends an audit row recording both actors, both hashes, and the timestamp

The caller (pre_commit_hook.py or the write adapter) invokes resolve_conflict()
ONLY when a write arrives on an entry whose on-disk content has already changed
since the actor last read it (hash mismatch with no held lock → race condition).

FM-7 guard: no silent overwrite is ever possible.

Language: Python stdlib only.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_SAFETY_DIR = Path(__file__).parent
_STORAGE_DIR = _SAFETY_DIR.parent / "storage"
sys.path.insert(0, str(_STORAGE_DIR))

from atomic_write import atomic_write  # noqa: E402
from frontmatter import parse_frontmatter, render_entry  # noqa: E402


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_conflict(
    store_root: Path,
    entry_id: str,
    competing_content: str,
    competing_actor: str,
    index: Any,  # DecisionIndex — passed in to avoid circular imports
) -> dict[str, str]:
    """
    Surface a write-race as a 🔶 Conflicted status.

    Parameters:
        store_root        — absolute path to the decision-log directory
        entry_id          — e.g. "D-9001"
        competing_content — full markdown text of the competing write
        competing_actor   — initials of the actor who produced competing_content
        index             — live DecisionIndex instance for audit writes

    Returns a dict:
        {
          "canonical_path": str,       # e.g. "D-9001.md"
          "conflict_path": str,        # e.g. "D-9001.conflict-RV-20260604T123456Z.md"
          "status": "conflicted",
          "canonical_actor": str,      # actor who wrote the canonical version
          "competing_actor": str,
        }

    Raises FileNotFoundError if the canonical entry doesn't exist.
    """
    canonical_path = store_root / f"{entry_id}.md"
    if not canonical_path.exists():
        raise FileNotFoundError(
            f"Cannot resolve conflict: canonical file not found: {canonical_path}"
        )

    # Read the canonical version
    canonical_text = canonical_path.read_text(encoding="utf-8")
    canonical_fm, canonical_body, errors = parse_frontmatter(canonical_text)
    if errors:
        raise ValueError(
            f"Cannot parse canonical file during conflict resolution: {errors}"
        )

    canonical_actor = canonical_fm.get("updated_by", "UNKNOWN")
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ts_slug = now_iso.replace(":", "").replace("-", "")  # 20260604T123456Z

    # Step 1: Write competing version to a .conflict sidecar file
    conflict_filename = f"{entry_id}.conflict-{competing_actor}-{ts_slug}.md"
    conflict_path = store_root / conflict_filename
    atomic_write(conflict_path, competing_content)

    # Step 2: Flip canonical status to "conflicted" and annotate body
    canonical_fm["status"] = "conflicted"
    canonical_fm["updated"] = now_iso
    canonical_fm["updated_by"] = "SYSTEM"

    conflict_note = (
        f"\n\n## Conflict ({now_iso})\n\n"
        f"**FM-7 guard:** concurrent write detected.\n\n"
        f"- **Canonical version** written by `{canonical_actor}` — preserved in `{entry_id}.md`\n"
        f"- **Competing version** written by `{competing_actor}` — preserved in `{conflict_filename}`\n\n"
        f"A RACI R/A holder must resolve this conflict and set status back to `answered` "
        f"(or the appropriate post-resolution status).\n"
    )
    updated_body = canonical_body.rstrip() + conflict_note

    updated_canonical = render_entry(canonical_fm, updated_body)
    from atomic_write import file_hash  # noqa: PLC0415
    canonical_before_hash = file_hash(canonical_path)
    canonical_after_hash = atomic_write(canonical_path, updated_canonical)

    # Step 3: Write conflict audit row
    _write_conflict_audit(
        index=index,
        entry_id=entry_id,
        canonical_actor=canonical_actor,
        competing_actor=competing_actor,
        canonical_before_hash=canonical_before_hash,
        canonical_after_hash=canonical_after_hash,
        conflict_filename=conflict_filename,
        now_iso=now_iso,
    )

    return {
        "canonical_path": f"{entry_id}.md",
        "conflict_path": conflict_filename,
        "status": "conflicted",
        "canonical_actor": canonical_actor,
        "competing_actor": competing_actor,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_conflict_audit(
    index: Any,
    entry_id: str,
    canonical_actor: str,
    competing_actor: str,
    canonical_before_hash: str,
    canonical_after_hash: str,
    conflict_filename: str,
    now_iso: str,
) -> None:
    """
    Append two audit rows:
      1. 'conflict' operation recording both actors and the sidecar filename
      2. 'write' operation for the status flip on the canonical file
    """
    con = index._con
    with con:
        # Primary conflict audit row
        con.execute(
            "INSERT INTO audit_log "
            "(entry_id, actor, operation, before_hash, after_hash, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry_id,
                f"{canonical_actor}+{competing_actor}",
                "conflict",
                canonical_before_hash,
                canonical_after_hash,
                now_iso,
            ),
        )
        # Secondary row: status flip write
        con.execute(
            "INSERT INTO audit_log "
            "(entry_id, actor, operation, before_hash, after_hash, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry_id,
                "SYSTEM",
                "write",
                canonical_before_hash,
                canonical_after_hash,
                now_iso,
            ),
        )
