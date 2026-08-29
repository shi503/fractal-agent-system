#!/usr/bin/env python3
"""
Regression test — the validator rejects a deliberately malformed entry.

Fixture: tests/malformed/D-BAD.md — combines five independent schema defects
(bad ID pattern, disallowed status, non-ISO-8601 timestamp, empty
raci.responsible, invalid/unknown initials) so the rejection is unambiguous.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).parent
_DL_ROOT = _TESTS_DIR.parent
_SCHEMA_DIR = _DL_ROOT / "schema"

sys.path.insert(0, str(_SCHEMA_DIR))

from validate import load_schema, load_people, validate_file  # noqa: E402

_MALFORMED_ENTRY = _TESTS_DIR / "malformed" / "D-BAD.md"


class TestMalformedEntryRejected(unittest.TestCase):

    def test_validate_file_rejects_malformed_entry(self) -> None:
        schema = load_schema()
        known_initials = load_people()
        ok, errors = validate_file(_MALFORMED_ENTRY, schema, known_initials)
        self.assertFalse(ok, "Malformed entry must not pass validation")
        self.assertTrue(errors, "Rejection must include at least one error message")

    def test_validate_cli_exits_nonzero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCHEMA_DIR / "validate.py"), str(_MALFORMED_ENTRY)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0, "CLI must exit non-zero on a malformed entry")
        self.assertIn("FAIL", result.stdout)

    def test_valid_fixtures_still_pass_for_contrast(self) -> None:
        """Sanity check: the rejection above is about this fixture's content,
        not the validator being broadly broken."""
        schema = load_schema()
        known_initials = load_people()
        fixtures_dir = _DL_ROOT / "schema" / "test-fixtures"
        for md_path in sorted(fixtures_dir.glob("*.md")):
            with self.subTest(fixture=md_path.name):
                ok, errors = validate_file(md_path, schema, known_initials)
                self.assertTrue(ok, f"{md_path.name} should validate cleanly: {errors}")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
