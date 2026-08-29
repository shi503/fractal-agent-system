#!/usr/bin/env python3
"""
Regression test — macOS symlinked-tmpdir portability bug.

Source defect (fixed here): `safety/pre_commit_hook.py`'s `run_hook()` computed
`store_root.relative_to(repo_root)` without resolving either path first.

`storage/store.py`'s `DecisionStore.__init__` always calls `.resolve()` on the
store root it is given. On macOS, a path under `/tmp` or `/var` commonly
resolves through a `/private/...` symlink (e.g. `tempfile.mkdtemp()` returns
`/var/folders/.../T/tmpXXXX`, whose resolved form is
`/private/var/folders/.../T/tmpXXXX`). If the *store root* passed to
`run_hook()` has been resolved (as `DecisionStore.root` always is) while the
*repo root* has not (as `git rev-parse --show-toplevel` may return the
unresolved form), `Path.relative_to()` raises `ValueError` even though the two
paths denote the same location on disk — the commit hook crashes on every
commit on an affected machine.

This test reproduces the divergence explicitly with a symlink, so it is not
dependent on macOS's specific `/var` -> `/private/var` layout and passes the
same way on any POSIX platform that supports symlinks (including the Linux
CI/dev boxes this suite also runs on).

Fix: `run_hook()` now calls `.resolve()` on both `store_root` and `repo_root`
before computing the relative prefix (see `safety/pre_commit_hook.py`).
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).parent
_DL_ROOT = _TESTS_DIR.parent
_SAFETY_DIR = _DL_ROOT / "safety"
_STORAGE_DIR = _DL_ROOT / "storage"

sys.path.insert(0, str(_STORAGE_DIR))
sys.path.insert(0, str(_SAFETY_DIR))

from pre_commit_hook import run_hook  # noqa: E402


@unittest.skipUnless(hasattr(os, "symlink"), "requires a POSIX platform with symlink support")
class TestSymlinkedTmpdirPortability(unittest.TestCase):
    """Reproduces the /var vs /private/var (or equivalent) divergence with an
    explicit symlink, so the fix is verified without depending on any one
    platform's specific temp-dir layout."""

    def setUp(self) -> None:
        # A real directory, plus a symlink that points at it — this stands in
        # for macOS's /var -> /private/var relationship, but works anywhere.
        self._real_parent = Path(tempfile.mkdtemp(prefix="dl-real-"))
        self._link_parent_container = Path(tempfile.mkdtemp(prefix="dl-link-container-"))
        self.symlinked_repo_root = self._link_parent_container / "repo-via-symlink"
        os.symlink(self._real_parent, self.symlinked_repo_root, target_is_directory=True)

        # decision-log/ created through the *unresolved* (symlinked) path —
        # this is what a caller would naturally construct from repo_root.
        store_root_unresolved = self.symlinked_repo_root / "decision-log"
        store_root_unresolved.mkdir(parents=True, exist_ok=True)

        # DecisionStore.__init__ always .resolve()s its root (storage/store.py).
        # We mimic that here directly, without needing sqlite: this is exactly
        # the value run_hook() receives as `store_root` in production.
        self.resolved_store_root = store_root_unresolved.resolve()

        # Sanity check: the whole point of this test is that these two forms
        # differ textually while denoting the same directory.
        self.assertNotEqual(
            str(self.resolved_store_root),
            str(store_root_unresolved),
            "Test setup did not actually create a path divergence — the "
            "symlink didn't introduce a distinct resolved form on this "
            "platform, so this test cannot exercise the bug here.",
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self._real_parent, ignore_errors=True)
        shutil.rmtree(self._link_parent_container, ignore_errors=True)

    def test_run_hook_survives_resolved_store_vs_unresolved_repo_root(self) -> None:
        """
        Before the fix: `store_root.relative_to(repo_root)` raised ValueError
        because store_root (resolved) and repo_root (unresolved, symlinked)
        have different textual prefixes despite denoting the same location.

        After the fix: run_hook() resolves both before comparing, so this
        call must complete and return 0 (no staged decision-log files).
        """
        rc = run_hook(
            store_root=self.resolved_store_root,
            staged_files=[],
            actor="AR",
            repo_root=self.symlinked_repo_root,  # deliberately unresolved
        )
        self.assertEqual(rc, 0)

    def test_run_hook_still_finds_staged_entries_under_the_symlink(self) -> None:
        """
        End-to-end: a staged decision-log file, referenced via the symlinked
        (unresolved) repo root, must still be recognised as being inside the
        store root once both sides are resolved.
        """
        entry_path = self.resolved_store_root / "D-9001.md"
        entry_path.write_text(
            "---\nid: D-9001\ntype: discovery\ntitle: t\nowner: AR\nstatus: open\n"
            "raci:\n  responsible: [AR]\ncreated: 2026-01-01T00:00:00Z\n"
            "updated: 2026-01-01T00:00:00Z\ncreated_by: AR\nupdated_by: AR\n---\n\nbody\n",
            encoding="utf-8",
        )
        # The staged path as a caller would naturally express it: relative to
        # the unresolved repo root.
        staged_rel = "decision-log/D-9001.md"

        rc = run_hook(
            store_root=self.resolved_store_root,
            staged_files=[staged_rel],
            actor="AR",
            repo_root=self.symlinked_repo_root,
        )
        # No lock held, no prior HEAD content (new file) → allowed (warn, not reject)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
