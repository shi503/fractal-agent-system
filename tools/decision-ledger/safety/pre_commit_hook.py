"""
Decision Ledger v2 — Pre-Commit Hook (concurrent-write guard)

Invoked by git pre-commit whenever a commit touches `decision-log/*.md`.
Enforces the same lock gate for scripted writers (the `dl` CLI) AND direct
editor saves (e.g. an Obsidian vault synced via obsidian-git) — both share
the same SQLite lock table.

Logic per staged entry:
  - Lock held by this actor   -> authorised, allow.
  - Lock held by different actor -> REJECT (exit 1).
  - No lock + another actor holds one -> conflict path -> resolve_conflict().
  - No lock + no contention   -> allow with warning (solo session).
  - Conflict sidecars (*.conflict-*.md) -> always allow through.

Environment:
    DL_STORE   — decision-log root override
    DL_ACTOR   — actor initials override (default: git config user.initials)

Language: Python stdlib only.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

_SAFETY_DIR = Path(__file__).parent
_STORAGE_DIR = _SAFETY_DIR.parent / "storage"
sys.path.insert(0, str(_STORAGE_DIR))

from atomic_write import file_hash  # noqa: E402
from store import DecisionStore  # noqa: E402

# Matches canonical entry filenames: D-9001.md, CD-1.md, BI-1.md, L2-01a.md
# Does NOT match sidecar: D-9001.conflict-AR-20260604T123456Z.md
_ENTRY_FILENAME_RE = re.compile(
    r'^(?:D-\d{1,4}[a-z]?|CD-\d{1,3}|BI-\d{1,3}|L\d{1,2}-\d{1,2}[a-z]?)\.md$'
)
_CONFLICT_SIDECAR_RE = re.compile(r'\.conflict-')


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        )
        return Path(out.decode().strip())
    except subprocess.CalledProcessError:
        return Path.cwd()


def _staged_files() -> list[str]:
    """Return list of staged file paths (relative to repo root)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            stderr=subprocess.DEVNULL,
        )
        return [p for p in out.decode().splitlines() if p.strip()]
    except subprocess.CalledProcessError:
        return []


def _head_content(rel_path: str) -> bytes | None:
    """Return HEAD content of *rel_path*, or None if it doesn't exist in HEAD."""
    try:
        return subprocess.check_output(
            ["git", "show", f"HEAD:{rel_path}"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def _git_actor() -> str:
    """Derive actor initials from git config or environment."""
    actor = os.environ.get("DL_ACTOR", "").strip()
    if actor:
        return actor
    try:
        out = subprocess.check_output(
            ["git", "config", "--get", "user.initials"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip() or "GIT"
    except subprocess.CalledProcessError:
        pass
    try:
        out = subprocess.check_output(
            ["git", "config", "--get", "user.name"],
            stderr=subprocess.DEVNULL,
        )
        name = out.decode().strip()
        # Build initials from first letters of each word
        return "".join(w[0].upper() for w in name.split() if w)[:4] or "GIT"
    except subprocess.CalledProcessError:
        return "GIT"


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def run_hook(
    store_root: Path,
    staged_files: list[str],
    actor: str,
    repo_root: Path,
) -> int:
    """
    Core hook logic. Returns 0 (allow commit) or 1 (reject commit).
    Pure function — testable without subprocess.
    """
    from conflict_resolver import resolve_conflict  # noqa: PLC0415

    # Portability: resolve both paths before computing a relative prefix.
    # On macOS, a store rooted under a tmp dir often resolves through a
    # /var -> /private/var symlink (tempfile.mkdtemp() returns the
    # unresolved /var/... form), while a repo root discovered via
    # `git rev-parse --show-toplevel` may come back unresolved too. If one
    # side is resolved and the other isn't, Path.relative_to() raises
    # ValueError even though the two paths denote the same location.
    # Resolving both sides here makes the prefix computation symlink-safe
    # on any platform, not just macOS.
    store_root = store_root.resolve()
    repo_root = repo_root.resolve()

    # Filter to decision-log/*.md files that are canonical entries
    dl_rel_prefix = store_root.relative_to(repo_root).as_posix() + "/"
    decision_log_files: list[tuple[str, str]] = []  # (rel_path, entry_id)

    for rel_path in staged_files:
        if not rel_path.startswith(dl_rel_prefix):
            continue
        filename = rel_path[len(dl_rel_prefix):]
        if _CONFLICT_SIDECAR_RE.search(filename):
            # Sidecar files created by conflict_resolver — always allow through
            continue
        if not _ENTRY_FILENAME_RE.match(filename):
            continue
        entry_id = filename[:-3]  # strip .md
        decision_log_files.append((rel_path, entry_id))

    if not decision_log_files:
        return 0  # no decision-log entries in this commit

    store = DecisionStore(store_root)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        for rel_path, entry_id in decision_log_files:
            abs_path = repo_root / rel_path

            # Compute staged hash
            staged_hash = file_hash(abs_path)

            # Get HEAD hash for this file
            head_bytes = _head_content(rel_path)
            head_hash = ""
            if head_bytes is not None:
                import hashlib
                head_hash = hashlib.sha256(head_bytes).hexdigest()

            is_new = head_hash == ""
            is_changed = staged_hash != head_hash

            # Check lock table
            lock = store.get_lock(entry_id)
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            if lock:
                held_by = lock["actor"]
                expires_at = lock["expires_at"]
                lock_active = expires_at > now_iso

                if lock_active and held_by != actor:
                    # REJECT: a different active actor holds the lock
                    errors.append(
                        f"  [LOCK CONFLICT] {entry_id}: locked by {held_by} until {expires_at}.\n"
                        f"    Your actor: {actor}. Commit rejected.\n"
                        f"    Resolve: wait for the lock to expire, or coordinate with {held_by}."
                    )
                    continue
                # Either same actor (authorised) or expired lock — allow through
                if lock_active and held_by == actor:
                    # Authorised write — allow; log will be written by the write path
                    pass
                else:
                    # Expired lock — warn but allow (solo sessions, lock TTL elapsed)
                    warnings.append(
                        f"  [WARN] {entry_id}: lock held by {held_by} has expired. "
                        f"Allowing commit by {actor}."
                    )
            else:
                # No lock — direct editor save bypassed the lock protocol
                if not is_new and is_changed:
                    # Check if there is any active lock held by anyone else
                    # (covers the race: actor B's direct save while A holds the lock
                    # but the inode wasn't visible to the lock table lookup above)
                    all_locks = store.query(
                        "SELECT id, actor, expires_at FROM locks WHERE id = ? AND expires_at > ?",
                        (entry_id, now_iso),
                    )
                    if all_locks:
                        other_lock = all_locks[0]
                        if other_lock["actor"] != actor:
                            # Concurrent-write guard: conflicting save — invoke conflict resolver
                            staged_content = abs_path.read_text(encoding="utf-8")
                            try:
                                result = resolve_conflict(
                                    store_root=store_root,
                                    entry_id=entry_id,
                                    competing_content=staged_content,
                                    competing_actor=actor,
                                    index=store._index,
                                )
                                errors.append(
                                    f"  [CONFLICT] {entry_id}: concurrent edit detected.\n"
                                    f"    Canonical version (by {result['canonical_actor']}) preserved "
                                    f"in {result['canonical_path']}\n"
                                    f"    Your version (by {actor}) preserved in {result['conflict_path']}\n"
                                    f"    Entry status flipped to conflicted.\n"
                                    f"    A RACI R/A holder must resolve. Commit rejected."
                                )
                            except Exception as exc:
                                errors.append(
                                    f"  [CONFLICT ERROR] {entry_id}: conflict resolution failed: {exc}"
                                )
                            continue
                    warnings.append(
                        f"  [WARN] {entry_id}: direct editor save (no lock held by {actor}). "
                        f"Allowed — no other actor holds an active lock. "
                        f"Consider using `dl lock {entry_id} --actor {actor}` before editing."
                    )

            # Regenerate active-locks view on every hook run that touches the lock table
            try:
                from active_locks_view import generate_active_locks_view  # noqa: PLC0415
                generate_active_locks_view(store_root)
            except Exception:
                pass  # View generation is best-effort; never block a commit

    finally:
        store.close()

    # Report warnings (non-blocking)
    if warnings:
        print("Decision Ledger pre-commit hook — warnings:", file=sys.stderr)
        for w in warnings:
            print(w, file=sys.stderr)

    # Report errors (blocking)
    if errors:
        print("\nDecision Ledger pre-commit hook — COMMIT REJECTED:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        print(
            "\nFix the issue and retry. For help: "
            "see tools/decision-ledger/safety/README.md",
            file=sys.stderr,
        )
        return 1

    return 0


def main() -> int:
    repo_root = _repo_root()

    # Determine store root
    store_env = os.environ.get("DL_STORE", "").strip()
    if store_env:
        store_root = Path(store_env).resolve()
    else:
        # Default: decision-log/ relative to repo root
        store_root = repo_root / "decision-log"

    if not store_root.exists():
        # No decision-log in this repo → skip hook silently
        return 0

    staged = _staged_files()
    actor = _git_actor()

    return run_hook(
        store_root=store_root,
        staged_files=staged,
        actor=actor,
        repo_root=repo_root,
    )


if __name__ == "__main__":
    sys.exit(main())
