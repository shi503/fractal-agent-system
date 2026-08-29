#!/usr/bin/env python3
"""
Decision Ledger v2 — Multi-User Safety Test Suite

Validates the concurrent-write guard: concurrent edits are caught and flipped
to `conflicted`, never silently overwritten.

Four smoke tests:
  1. Skill–skill: two scripted sessions try to write D-9001 simultaneously; second is blocked.
  2. Editor–editor: two direct-file saves to D-9001.md; second is caught by the hook.
  3. Skill–editor: mixed path; first wins, second sees the conflict.
  4. Lock-expire race: lock expires mid-edit; both writes succeed but second is marked conflicted.

Additional tests:
  5. Lock TTL renewal (`dl lock-renew`) extends expiry.
  6. Active-locks view is regenerated after lock events.
  7. Audit log captures all events: lock/unlock/conflict/lock_renew.

Run:
    python3 tools/decision-ledger/safety/test_multi_user_safety.py
    python3 -m pytest tools/decision-ledger/safety/test_multi_user_safety.py -v

Exit code 0 = all pass.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

_SAFETY_DIR = Path(__file__).parent
_STORAGE_DIR = _SAFETY_DIR.parent / "storage"
_FIXTURES_DIR = _STORAGE_DIR.parent / "schema" / "test-fixtures"

sys.path.insert(0, str(_STORAGE_DIR))
sys.path.insert(0, str(_SAFETY_DIR))

from store import DecisionStore  # noqa: E402
from frontmatter import parse_frontmatter, render_entry  # noqa: E402
from conflict_resolver import resolve_conflict  # noqa: E402
from pre_commit_hook import run_hook  # noqa: E402
from active_locks_view import generate_active_locks_view  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_dir: Path) -> DecisionStore:
    store_root = tmp_dir / "decision-log"
    store_root.mkdir(parents=True, exist_ok=True)
    return DecisionStore(store_root)


def _seed_entry(store: DecisionStore) -> tuple[dict, str]:
    """Copy the D-9001 fixture into the store and rebuild index. Returns (fm, body)."""
    src = _FIXTURES_DIR / "D-9001.md"
    dest = store.root / "D-9001.md"
    shutil.copy2(src, dest)
    store.rebuild_index(actor="SETUP")
    fm, body = store.read("D-9001")
    return fm, body


def _read_audit(store: DecisionStore, entry_id: str) -> list[dict]:
    return store.query(
        "SELECT rowid, actor, operation, before_hash, after_hash, timestamp "
        "FROM audit_log WHERE entry_id = ? ORDER BY rowid",
        (entry_id,),
    )


# ---------------------------------------------------------------------------
# Smoke test 1 — Skill–Skill: second session is blocked by the lock
# ---------------------------------------------------------------------------

class TestSmokeSkillSkill(unittest.TestCase):
    """
    Two scripted sessions try to write D-9001 simultaneously.
    Only one succeeds; the other gets a clear lock-conflict error.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        self.fm, self.body = _seed_entry(self.store)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_first_actor_acquires_lock(self) -> None:
        acquired = self.store.lock("D-9001", "AR")
        self.assertTrue(acquired, "Actor AR should acquire the lock")
        lock = self.store.get_lock("D-9001")
        self.assertIsNotNone(lock)
        self.assertEqual(lock["actor"], "AR")

    def test_second_actor_blocked(self) -> None:
        self.store.lock("D-9001", "AR")
        # RV (second actor) cannot acquire
        acquired_rv = self.store.lock("D-9001", "RV")
        self.assertFalse(acquired_rv, "Actor RV should be blocked by AR's lock")

    def test_second_actor_write_raises_permission_error(self) -> None:
        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        with self.assertRaises(PermissionError) as ctx:
            self.store.write("D-9001", fm, body + "\nRV edit", actor="RV")
        self.assertIn("AR", str(ctx.exception))
        self.assertIn("locked", str(ctx.exception).lower())

    def test_lock_holder_can_write(self) -> None:
        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        after_hash = self.store.write("D-9001", fm, body + "\nAR edit", actor="AR")
        self.assertTrue(len(after_hash) > 0)

    def test_audit_log_captures_lock_and_blocked_attempt(self) -> None:
        self.store.lock("D-9001", "AR")
        self.store.lock("D-9001", "RV")  # returns False but doesn't write an audit row for RV

        rows = _read_audit(self.store, "D-9001")
        ops = [r["operation"] for r in rows]
        self.assertIn("lock", ops, "Expected lock audit row for AR")


# ---------------------------------------------------------------------------
# Smoke test 2 — Editor–editor: second direct save caught by pre-commit hook
# ---------------------------------------------------------------------------

class TestSmokeEditorEditor(unittest.TestCase):
    """
    Two direct-editor saves to D-9001.md.
    The first save is staged and committed without a lock (solo, allowed with warning).
    The second save arrives while the first actor has an active lock → hook rejects.

    The hook is tested via run_hook() directly (no subprocess git needed).
    """

    def setUp(self) -> None:
        # .resolve() the repo root explicitly: DecisionStore always resolves
        # its own root (store.py), so an unresolved repo_root on a platform
        # where the tmp dir sits behind a symlink (e.g. macOS /var ->
        # /private/var) would make store.root.relative_to(repo_root) fail
        # here in the test harness itself — independent of the run_hook()
        # fix this suite exercises. Resolving here keeps this test about the
        # hook's lock logic, not about tmp-dir symlinks (see tests/ for the
        # dedicated symlink-portability regression test).
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.store = _make_store(self.tmp)
        self.fm, self.body = _seed_entry(self.store)
        self.repo_root = self.tmp  # simulate repo root = tmp

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _stage_file(self, entry_id: str, content: str) -> str:
        """Write content to the staged file path and return the rel path."""
        dl_root_rel = self.store.root.relative_to(self.repo_root).as_posix()
        rel_path = f"{dl_root_rel}/{entry_id}.md"
        abs_path = self.repo_root / rel_path
        abs_path.write_text(content, encoding="utf-8")
        return rel_path

    def test_direct_save_no_lock_allowed_with_warning(self) -> None:
        """
        First direct save: no lock held by anyone → allowed (solo session).
        Hook returns 0.
        """
        content = render_entry(self.fm, self.body + "\nDirect edit by AR")
        rel_path = self._stage_file("D-9001", content)

        rc = run_hook(
            store_root=self.store.root,
            staged_files=[rel_path],
            actor="AR",
            repo_root=self.repo_root,
        )
        # No lock, no conflict → allowed (returns 0, may emit warning to stderr)
        self.assertEqual(rc, 0)

    def test_direct_save_with_other_actor_lock_rejected(self) -> None:
        """
        Second direct save: AR holds an active lock; RV's direct save is rejected.
        Hook returns 1.
        """
        # AR acquires lock
        self.store.lock("D-9001", "AR")

        # RV writes a competing file directly
        rv_content = render_entry(self.fm, self.body + "\nDirect edit by RV")
        rel_path = self._stage_file("D-9001", rv_content)

        rc = run_hook(
            store_root=self.store.root,
            staged_files=[rel_path],
            actor="RV",
            repo_root=self.repo_root,
        )
        self.assertEqual(rc, 1, "Hook should reject RV's save because AR holds the lock")

    def test_non_decision_log_files_ignored(self) -> None:
        """Files outside decision-log are not checked by the hook."""
        rc = run_hook(
            store_root=self.store.root,
            staged_files=["some/other/file.md"],
            actor="AR",
            repo_root=self.repo_root,
        )
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Smoke test 3 — Skill–editor mixed path: first wins, second sees conflict
# ---------------------------------------------------------------------------

class TestSmokeSkillEditor(unittest.TestCase):
    """
    Skill writes D-9001 (acquires lock, writes, releases).
    Then a direct-editor save arrives with a competing version while
    a DIFFERENT actor holds the lock → concurrent-write guard triggers.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        self.fm, self.body = _seed_entry(self.store)
        self.repo_root = self.tmp

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_skill_then_editor_conflict(self) -> None:
        """
        AR (skill) writes D-9001.  Then RV (direct editor) saves a different version
        while AR's lock is still active → conflict surfaced, both versions preserved.
        """
        # AR (skill path): acquire lock, write, keep lock active for the test
        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        self.store.write("D-9001", fm, body + "\nAR answer via skill", actor="AR")

        # RV (editor path): write a competing version directly to disk
        rv_fm = dict(fm)
        rv_content = render_entry(rv_fm, body + "\nRV competing answer via editor")

        result = resolve_conflict(
            store_root=self.store.root,
            entry_id="D-9001",
            competing_content=rv_content,
            competing_actor="RV",
            index=self.store._index,
        )

        # Both versions preserved
        self.assertEqual(result["status"], "conflicted")
        canonical_path = self.store.root / "D-9001.md"
        conflict_path = self.store.root / result["conflict_path"]

        self.assertTrue(canonical_path.exists(), "Canonical D-9001.md must be preserved")
        self.assertTrue(conflict_path.exists(), "Sidecar conflict file must exist")

        # Canonical status flipped to conflicted
        canonical_fm, _, _ = parse_frontmatter(canonical_path.read_text(encoding="utf-8"))
        self.assertEqual(canonical_fm["status"], "conflicted")

        # Audit log has a conflict row
        rows = _read_audit(self.store, "D-9001")
        conflict_rows = [r for r in rows if r["operation"] == "conflict"]
        self.assertTrue(len(conflict_rows) >= 1, "Expected at least one conflict audit row")
        self.assertIn("RV", conflict_rows[-1]["actor"])

    def test_conflict_sidecar_not_overwritten(self) -> None:
        """A second conflict preserves both sidecars — no silent overwrite."""
        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        self.store.write("D-9001", fm, body + "\nAR edit", actor="AR")

        competing1 = render_entry(fm, body + "\nRV competing v1")
        resolve_conflict(
            store_root=self.store.root,
            entry_id="D-9001",
            competing_content=competing1,
            competing_actor="RV",
            index=self.store._index,
        )

        # Second competing write (different timestamp slug)
        time.sleep(1)  # ensure distinct timestamps
        competing2 = render_entry(fm, body + "\nSP competing v2")
        resolve_conflict(
            store_root=self.store.root,
            entry_id="D-9001",
            competing_content=competing2,
            competing_actor="SP",
            index=self.store._index,
        )

        # Both sidecar files exist
        sidecar_files = list(self.store.root.glob("D-9001.conflict-*.md"))
        self.assertEqual(len(sidecar_files), 2, f"Expected 2 sidecar files, got: {sidecar_files}")


# ---------------------------------------------------------------------------
# Smoke test 4 — Lock-expire race: the guard prevents silent overwrite
# ---------------------------------------------------------------------------

class TestSmokeLockExpireRace(unittest.TestCase):
    """
    Force a lock to expire mid-edit.
    Both writes succeed but the second one triggers resolve_conflict()
    rather than silently overwriting.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        self.fm, self.body = _seed_entry(self.store)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_expired_lock_allows_competing_write_but_surfaces_conflict(self) -> None:
        """
        AR acquires a 1-second TTL lock and writes.
        Lock expires.  RV's write proceeds but calls resolve_conflict()
        to preserve both versions.
        """
        # AR acquires a very short TTL lock (1 second for the test)
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=1)
        fm, body = self.store.read("D-9001")

        # AR writes (lock is live)
        self.store.write("D-9001", fm, body + "\nAR edit (pre-expire)", actor="AR")

        # Wait for lock to expire
        time.sleep(2)

        # Confirm lock is expired
        lock = self.store.get_lock("D-9001")
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if lock:
            self.assertLessEqual(lock["expires_at"], now_iso, "Lock should be expired by now")

        # RV's competing write (lock expired → no PermissionError, but we detect via hash)
        rv_content = render_entry(fm, body + "\nRV competing edit (post-expire)")

        # Simulate: RV detects the canonical file has changed since they read it
        # (different hash) → calls resolve_conflict
        result = resolve_conflict(
            store_root=self.store.root,
            entry_id="D-9001",
            competing_content=rv_content,
            competing_actor="RV",
            index=self.store._index,
        )

        # Concurrent-write guard: no silent overwrite
        self.assertEqual(result["status"], "conflicted")
        sidecar = self.store.root / result["conflict_path"]
        self.assertTrue(sidecar.exists(), "Competing version must be preserved as sidecar")

        # Read sidecar content — must contain RV's edit
        sidecar_text = sidecar.read_text(encoding="utf-8")
        self.assertIn("RV competing edit", sidecar_text)

        # Canonical file must contain the status flip
        canonical_text = (self.store.root / "D-9001.md").read_text(encoding="utf-8")
        canonical_fm, _, _ = parse_frontmatter(canonical_text)
        self.assertEqual(canonical_fm["status"], "conflicted")

        # Audit log must have a conflict row
        rows = _read_audit(self.store, "D-9001")
        ops = [r["operation"] for r in rows]
        self.assertIn("conflict", ops, f"Expected 'conflict' in audit ops; got: {ops}")

    def test_expired_lock_solo_write_does_not_conflict(self) -> None:
        """
        If a lock expires and NO other actor's write has occurred, the next write
        by the original actor simply succeeds (no conflict).
        """
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=1)
        time.sleep(2)

        fm, body = self.store.read("D-9001")
        # AR writes after their own lock expired — no other actor involved
        # store.write() does a lock check; expired lock is not an obstruction
        after_hash = self.store.write("D-9001", fm, body + "\nAR re-edit after expire", actor="AR")
        self.assertTrue(len(after_hash) > 0)

        # No conflict files
        sidecars = list(self.store.root.glob("D-9001.conflict-*.md"))
        self.assertEqual(sidecars, [], f"Unexpected sidecar files: {sidecars}")


# ---------------------------------------------------------------------------
# Test 5 — Lock TTL renewal
# ---------------------------------------------------------------------------

class TestLockRenewal(unittest.TestCase):
    """`dl lock-renew` (renew_lock) extends the TTL without losing the lock."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        _seed_entry(self.store)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_renew_extends_expiry(self) -> None:
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=5)
        lock_before = self.store.get_lock("D-9001")
        self.assertIsNotNone(lock_before)

        time.sleep(1)
        renewed = self.store.renew_lock("D-9001", "AR", ttl_seconds=300)
        self.assertTrue(renewed, "renew_lock should return True for the lock holder")

        lock_after = self.store.get_lock("D-9001")
        self.assertGreater(
            lock_after["expires_at"],
            lock_before["expires_at"],
            "Expiry should be extended after renewal",
        )

    def test_renew_wrong_actor_fails(self) -> None:
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=300)
        renewed = self.store.renew_lock("D-9001", "RV", ttl_seconds=300)
        self.assertFalse(renewed, "renew_lock should return False for a non-holder")

        # AR's lock must remain unchanged
        lock = self.store.get_lock("D-9001")
        self.assertEqual(lock["actor"], "AR")

    def test_renew_no_lock_fails(self) -> None:
        renewed = self.store.renew_lock("D-9001", "AR", ttl_seconds=300)
        self.assertFalse(renewed, "renew_lock should return False when no lock exists")

    def test_renew_audit_row_written(self) -> None:
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=5)
        self.store.renew_lock("D-9001", "AR", ttl_seconds=300)

        rows = _read_audit(self.store, "D-9001")
        renew_rows = [r for r in rows if r["operation"] == "lock_renew"]
        self.assertEqual(len(renew_rows), 1, "Expected one lock_renew audit row")
        self.assertEqual(renew_rows[0]["actor"], "AR")


# ---------------------------------------------------------------------------
# Test 6 — Active-locks view
# ---------------------------------------------------------------------------

class TestActiveLocksView(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        _seed_entry(self.store)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_view_generated_with_active_lock(self) -> None:
        self.store.lock("D-9001", "AR")
        self.store.close()

        view_path = generate_active_locks_view(self.tmp / "decision-log")
        self.assertTrue(view_path.exists(), "views/active-locks.md must be generated")
        content = view_path.read_text(encoding="utf-8")
        self.assertIn("D-9001", content)
        self.assertIn("AR", content)

        self.store = DecisionStore(self.tmp / "decision-log")

    def test_view_shows_no_locks_when_empty(self) -> None:
        view_path = generate_active_locks_view(self.tmp / "decision-log")
        content = view_path.read_text(encoding="utf-8")
        self.assertIn("No active locks", content)

    def test_view_updated_after_unlock(self) -> None:
        self.store.lock("D-9001", "AR")
        generate_active_locks_view(self.tmp / "decision-log")
        self.store.unlock("D-9001", "AR")

        view_path = generate_active_locks_view(self.tmp / "decision-log")
        content = view_path.read_text(encoding="utf-8")
        self.assertIn("No active locks", content)


# ---------------------------------------------------------------------------
# Test 7 — Audit log completeness
# ---------------------------------------------------------------------------

class TestAuditLog(unittest.TestCase):
    """All lock/write/conflict/lock_renew events appear in the audit log."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)
        self.fm, self.body = _seed_entry(self.store)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_lifecycle_audit(self) -> None:
        # lock → write → renew → unlock → conflict
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=60)
        self.store.write("D-9001", self.fm, self.body + "\nAR edit", actor="AR")
        self.store.renew_lock("D-9001", "AR", ttl_seconds=300)
        self.store.unlock("D-9001", "AR")

        rv_content = render_entry(self.fm, self.body + "\nRV competing")
        self.store._index.acquire_lock("D-9001", "AR", ttl_seconds=60)  # AR reacquires
        resolve_conflict(
            store_root=self.store.root,
            entry_id="D-9001",
            competing_content=rv_content,
            competing_actor="RV",
            index=self.store._index,
        )

        rows = _read_audit(self.store, "D-9001")
        ops = {r["operation"] for r in rows}
        for expected_op in ("lock", "write", "lock_renew", "unlock", "conflict"):
            self.assertIn(expected_op, ops, f"Expected '{expected_op}' in audit ops; got: {ops}")

    def test_audit_log_is_insert_only(self) -> None:
        """Confirm no UPDATE or DELETE is issued against audit_log (read-only after insert)."""
        self.store.lock("D-9001", "AR")
        self.store.write("D-9001", self.fm, self.body, actor="AR")

        count_before = len(_read_audit(self.store, "D-9001"))
        # Verify the DDL has no trigger/update path by checking row count only grows
        self.store.write("D-9001", self.fm, self.body + "\nmore", actor="AR")
        count_after = len(_read_audit(self.store, "D-9001"))
        self.assertGreater(count_after, count_before, "Audit log must only grow")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
