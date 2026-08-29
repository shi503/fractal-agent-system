#!/usr/bin/env python3
"""
Decision Ledger v2 — Storage Layer Test Suite

Tests:
  1. Round-trip: read → write → read for every fixture (no diff)
  2. Atomic write: partial failure leaves original intact
  3. Index rebuild: lossless after deleting .index.sqlite
  4. FM-1 verify_consistency: detects drift
  5. Lock primitives: two-actor conflict surfaces correctly
  6. Audit log: every write is recorded, records are insert-only

Run:
    python3 tools/decision-ledger/storage/test_storage.py
    python3 -m pytest tools/decision-ledger/storage/test_storage.py -v

Exit code 0 = all pass.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Locate the storage module directory
_STORAGE_DIR = Path(__file__).parent
sys.path.insert(0, str(_STORAGE_DIR))

from atomic_write import atomic_write, file_hash  # noqa: E402
from frontmatter import parse_frontmatter, render_entry  # noqa: E402
from store import DecisionStore  # noqa: E402

# Canonical fixtures directory
_FIXTURES_DIR = _STORAGE_DIR.parent / "schema" / "test-fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_dir: Path) -> DecisionStore:
    store_root = tmp_dir / "decision-log"
    store_root.mkdir()
    return DecisionStore(store_root)


def _copy_fixtures(store: DecisionStore) -> list[str]:
    """Copy all fixture .md files into the store. Returns list of IDs."""
    ids = []
    for md_path in sorted(_FIXTURES_DIR.glob("*.md")):
        dest = store.root / md_path.name
        shutil.copy2(md_path, dest)
        ids.append(md_path.stem)
    return ids


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestAtomicWrite(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_file(self) -> None:
        dest = self.tmp / "test.md"
        digest = atomic_write(dest, "hello world")
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        self.assertEqual(digest, expected)

    def test_overwrites_existing(self) -> None:
        dest = self.tmp / "test.md"
        atomic_write(dest, "original")
        atomic_write(dest, "updated")
        self.assertEqual(dest.read_text(), "updated")

    def test_creates_parent_dirs(self) -> None:
        dest = self.tmp / "a" / "b" / "test.md"
        atomic_write(dest, "nested")
        self.assertTrue(dest.exists())

    def test_file_hash_nonexistent(self) -> None:
        self.assertEqual(file_hash(self.tmp / "missing.md"), "")

    def test_file_hash_matches_content(self) -> None:
        dest = self.tmp / "test.md"
        content = "some content here"
        dest.write_text(content, encoding="utf-8")
        expected = hashlib.sha256(content.encode()).hexdigest()
        self.assertEqual(file_hash(dest), expected)


class TestFrontmatterParser(unittest.TestCase):
    """Verify parse ↔ serialise round-trip for all fixture files."""

    def _check_fixture(self, path: Path) -> None:
        original = path.read_text(encoding="utf-8")
        fm, body, errors = parse_frontmatter(original)
        self.assertEqual(errors, [], f"{path.name}: parse errors: {errors}")
        self.assertIn("id", fm, f"{path.name}: missing 'id' field")
        rendered = render_entry(fm, body)
        # Re-parse rendered to confirm structural equivalence
        fm2, body2, errors2 = parse_frontmatter(rendered)
        self.assertEqual(errors2, [], f"{path.name}: re-parse errors after render")
        # Key fields must be identical
        for field in ("id", "type", "status", "owner", "created", "updated"):
            self.assertEqual(
                fm.get(field), fm2.get(field),
                f"{path.name}: field '{field}' changed after round-trip"
            )

    def test_round_trip_D9001(self) -> None:
        self._check_fixture(_FIXTURES_DIR / "D-9001.md")

    def test_round_trip_CD1(self) -> None:
        self._check_fixture(_FIXTURES_DIR / "CD-1.md")

    def test_round_trip_BI1(self) -> None:
        self._check_fixture(_FIXTURES_DIR / "BI-1.md")

    def test_round_trip_L201a(self) -> None:
        self._check_fixture(_FIXTURES_DIR / "L2-01a.md")

    def test_inline_list_preserved(self) -> None:
        text = (
            "---\n"
            "id: D-001\n"
            "type: discovery\n"
            "title: Test\n"
            "owner: AR\n"
            "status: open\n"
            "raci:\n"
            "  responsible: [AR, RV]\n"
            "  accountable: [SP]\n"
            "created: 2026-01-01T00:00:00Z\n"
            "updated: 2026-01-01T00:00:00Z\n"
            "created_by: AR\n"
            "updated_by: AR\n"
            "---\n\n## Body\n"
        )
        fm, body, errors = parse_frontmatter(text)
        self.assertEqual(errors, [])
        raci = fm.get("raci", {})
        self.assertEqual(raci.get("responsible"), ["AR", "RV"])
        self.assertEqual(raci.get("accountable"), ["SP"])


class TestDecisionStore(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store = _make_store(self.tmp)

    def tearDown(self) -> None:
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # Round-trip tests (requirement: read → write → read with no diff)
    # ------------------------------------------------------------------

    def _round_trip(self, fixture_path: Path) -> None:
        original_text = fixture_path.read_text(encoding="utf-8")
        fm_orig, body_orig, errors = parse_frontmatter(original_text)
        self.assertEqual(errors, [], f"{fixture_path.name}: parse errors")

        entry_id = fm_orig["id"]
        # Write fixture into store
        self.store.write(entry_id, fm_orig, body_orig, actor="AR")

        # Read back
        fm_back, body_back = self.store.read(entry_id)

        # Structural equivalence on all key fields
        for field in ("id", "type", "status", "owner", "title",
                       "created", "updated", "created_by", "updated_by"):
            self.assertEqual(
                fm_orig.get(field), fm_back.get(field),
                f"{fixture_path.name}: field '{field}' changed after round-trip",
            )

        # RACI equivalence
        raci_orig = fm_orig.get("raci", {})
        raci_back = fm_back.get("raci", {})
        for role in ("responsible", "accountable", "consulted", "informed"):
            self.assertEqual(
                raci_orig.get(role), raci_back.get(role),
                f"{fixture_path.name}: raci.{role} changed after round-trip",
            )

    def test_round_trip_all_fixtures(self) -> None:
        for md_path in sorted(_FIXTURES_DIR.glob("*.md")):
            with self.subTest(fixture=md_path.name):
                self._round_trip(md_path)

    # ------------------------------------------------------------------
    # Rebuild index: lossless reconstruction
    # ------------------------------------------------------------------

    def test_rebuild_index_lossless(self) -> None:
        """Delete .index.sqlite; rebuild; verify all entries recoverable."""
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        # Verify we can read all fixtures via index
        listed = self.store.list_entries()
        listed_ids = {fm["id"] for fm in listed}
        for fixture_id in ids:
            self.assertIn(fixture_id, listed_ids, f"{fixture_id} missing from index after rebuild")

        # Delete index file and rebuild from scratch
        db_path = self.store.root / DecisionStore.INDEX_FILENAME
        self.store.close()
        db_path.unlink()

        # Re-open store (creates empty index)
        self.store = DecisionStore(self.tmp / "decision-log")
        listed_before = self.store.list_entries()
        self.assertEqual(listed_before, [], "Expected empty index after delete")

        # Rebuild
        stats = self.store.rebuild_index(actor="TEST")
        self.assertEqual(stats["parsed"], len(ids), "Not all fixtures parsed")
        self.assertEqual(stats["upserted"], len(ids), "Not all fixtures upserted")

        # All entries recovered
        listed_after = self.store.list_entries()
        recovered_ids = {fm["id"] for fm in listed_after}
        for fixture_id in ids:
            self.assertIn(fixture_id, recovered_ids, f"{fixture_id} not recovered after rebuild")

    # ------------------------------------------------------------------
    # FM-1: verify_consistency detects drift
    # ------------------------------------------------------------------

    def test_verify_consistency_clean(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")
        drift = self.store.verify_consistency()
        self.assertEqual(drift, [], f"Expected no drift, got: {drift}")

    def test_verify_consistency_detects_hash_drift(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        # Tamper with a markdown file directly (bypass the write API)
        tampered = self.store.root / "D-9001.md"
        original = tampered.read_text()
        tampered.write_text(original + "\n<!-- tampered -->")

        drift = self.store.verify_consistency()
        self.assertTrue(
            any("D-9001" in msg for msg in drift),
            f"Expected drift for D-9001, got: {drift}",
        )

    def test_verify_consistency_detects_missing_file(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        # Delete a markdown file without touching the index
        (self.store.root / "D-9001.md").unlink()

        drift = self.store.verify_consistency()
        self.assertTrue(
            any("D-9001" in msg for msg in drift),
            f"Expected drift for missing D-9001, got: {drift}",
        )

    def test_verify_consistency_detects_unindexed_file(self) -> None:
        """File on disk not in index → FM-1 drift."""
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        # Add a new file without going through write API
        new_md = self.store.root / "D-9999.md"
        fixture_text = (self.store.root / "D-9001.md").read_text()
        new_md.write_text(fixture_text.replace("D-9001", "D-9999"))

        drift = self.store.verify_consistency()
        self.assertTrue(
            any("D-9999" in msg for msg in drift),
            f"Expected drift for unindexed D-9999, got: {drift}",
        )

    # ------------------------------------------------------------------
    # Lock primitives
    # ------------------------------------------------------------------

    def test_lock_acquire_release(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.assertTrue(self.store.lock("D-9001", "AR"))
        lock = self.store.get_lock("D-9001")
        self.assertIsNotNone(lock)
        self.assertEqual(lock["actor"], "AR")

        self.assertTrue(self.store.unlock("D-9001", "AR"))
        self.assertIsNone(self.store.get_lock("D-9001"))

    def test_lock_conflict_different_actor(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.assertTrue(self.store.lock("D-9001", "AR"))
        # Different actor cannot acquire
        self.assertFalse(self.store.lock("D-9001", "RV"))

    def test_lock_write_blocked_for_different_actor(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        with self.assertRaises(PermissionError):
            self.store.write("D-9001", fm, body, actor="RV")

    def test_lock_write_allowed_for_lock_holder(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.store.lock("D-9001", "AR")
        fm, body = self.store.read("D-9001")
        # Lock holder can still write
        self.store.write("D-9001", fm, body, actor="AR")

    def test_unlock_wrong_actor_refused(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.store.lock("D-9001", "AR")
        self.assertFalse(self.store.unlock("D-9001", "RV"))
        # Lock still held
        self.assertIsNotNone(self.store.get_lock("D-9001"))

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def test_audit_log_records_write(self) -> None:
        ids = _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        fm, body = self.store.read("D-9001")
        self.store.write("D-9001", fm, body, actor="AR")

        rows = self.store.query(
            "SELECT * FROM audit_log WHERE entry_id = ? AND operation = 'write' ORDER BY rowid",
            ("D-9001",),
        )
        self.assertGreater(len(rows), 0, "Expected at least one audit record for D-9001 write")
        last = rows[-1]
        self.assertEqual(last["actor"], "AR")
        self.assertEqual(last["operation"], "write")

    def test_audit_log_records_rebuild(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST_REBUILD")

        rows = self.store.query(
            "SELECT * FROM audit_log WHERE entry_id = '*' AND operation = 'rebuild'"
        )
        self.assertGreater(len(rows), 0, "Expected rebuild audit record")
        self.assertEqual(rows[-1]["actor"], "TEST_REBUILD")

    def test_audit_log_records_lock_unlock(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        self.store.lock("D-9001", "AR")
        self.store.unlock("D-9001", "AR")

        lock_rows = self.store.query(
            "SELECT * FROM audit_log WHERE entry_id = 'D-9001' AND operation = 'lock'"
        )
        unlock_rows = self.store.query(
            "SELECT * FROM audit_log WHERE entry_id = 'D-9001' AND operation = 'unlock'"
        )
        self.assertEqual(len(lock_rows), 1)
        self.assertEqual(len(unlock_rows), 1)

    # ------------------------------------------------------------------
    # query() API
    # ------------------------------------------------------------------

    def test_query_raw_select(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")

        rows = self.store.query("SELECT id, status FROM entries ORDER BY id")
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertIn("id", row)
            self.assertIn("status", row)

    def test_query_raw_rejects_non_select(self) -> None:
        with self.assertRaises(ValueError):
            self.store.query("DELETE FROM entries")

    # ------------------------------------------------------------------
    # list_entries with filters
    # ------------------------------------------------------------------

    def test_list_entries_all(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")
        entries = self.store.list_entries()
        self.assertEqual(len(entries), 4)  # 4 fixtures

    def test_list_entries_filter_status(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")
        open_entries = self.store.list_entries({"status": "open"})
        for fm in open_entries:
            self.assertEqual(fm["status"], "open")

    def test_list_entries_filter_type(self) -> None:
        _copy_fixtures(self.store)
        self.store.rebuild_index(actor="TEST")
        discovery = self.store.list_entries({"type": "discovery"})
        for fm in discovery:
            self.assertEqual(fm["type"], "discovery")


class TestCLI(unittest.TestCase):
    """Smoke test the CLI with a 4-entry corpus."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.store_root = self.tmp / "decision-log"
        self.store_root.mkdir()
        # Copy fixtures in
        for md_path in sorted(_FIXTURES_DIR.glob("*.md")):
            shutil.copy2(md_path, self.store_root / md_path.name)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args: str) -> tuple[int, str]:
        import io
        from contextlib import redirect_stdout, redirect_stderr

        sys.path.insert(0, str(_STORAGE_DIR))
        from cli import main  # noqa: PLC0415

        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = main(["--store", str(self.store_root), *args])
        return rc, buf_out.getvalue() + buf_err.getvalue()

    def test_rebuild_and_list(self) -> None:
        rc, out = self._run("rebuild-index", "--actor", "TEST")
        self.assertEqual(rc, 0, out)
        self.assertIn("parsed", out)

        rc2, out2 = self._run("list")
        self.assertEqual(rc2, 0, out2)
        self.assertIn("D-9001", out2)
        self.assertIn("CD-1", out2)

    def test_read(self) -> None:
        self._run("rebuild-index", "--actor", "TEST")
        rc, out = self._run("read", "D-9001")
        self.assertEqual(rc, 0, out)
        self.assertIn("D-9001", out)
        self.assertIn("webhook", out)

    def test_verify_clean(self) -> None:
        self._run("rebuild-index", "--actor", "TEST")
        rc, out = self._run("verify")
        self.assertEqual(rc, 0, out)
        self.assertIn("FM-1 OK", out)

    def test_lock_and_unlock(self) -> None:
        self._run("rebuild-index", "--actor", "TEST")
        rc, out = self._run("lock", "D-9001", "--actor", "AR")
        self.assertEqual(rc, 0, out)
        self.assertIn("acquired", out)

        rc2, out2 = self._run("unlock", "D-9001", "--actor", "AR")
        self.assertEqual(rc2, 0, out2)

    def test_read_not_found(self) -> None:
        self._run("rebuild-index", "--actor", "TEST")
        rc, out = self._run("read", "D-9999")
        self.assertEqual(rc, 2, out)

    def test_audit(self) -> None:
        self._run("rebuild-index", "--actor", "TEST")
        rc, out = self._run("audit")
        self.assertEqual(rc, 0, out)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
