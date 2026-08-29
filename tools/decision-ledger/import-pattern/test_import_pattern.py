#!/usr/bin/env python3
"""
Decision Ledger v2 — Import Pattern Test Suite

Covers the generic v1-table helpers (v1_pattern.py) plus the one worked
example (convert_v1_sample.py) that converts
`fixtures/taskflow/v1-sample.md` into a schema-valid v2 entry.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_IMPORT_PATTERN_DIR = Path(__file__).parent
_DL_ROOT = _IMPORT_PATTERN_DIR.parent
_SCHEMA_DIR = _DL_ROOT / "schema"

for _d in (_IMPORT_PATTERN_DIR, _SCHEMA_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import v1_pattern as vp  # noqa: E402
from convert_v1_sample import convert, _DEFAULT_SOURCE, _PEOPLE_YAML  # noqa: E402
from validate import load_schema, validate_file  # noqa: E402
from frontmatter import render_entry  # noqa: E402


class TestStatusMapping(unittest.TestCase):

    def test_emoji_wins_over_text(self) -> None:
        self.assertEqual(vp.parse_status("🟢 Answered — details"), "answered")

    def test_text_fallback(self) -> None:
        self.assertEqual(vp.parse_status("In Discovery, no emoji"), "in_discovery")

    def test_unknown_defaults_open(self) -> None:
        self.assertEqual(vp.parse_status("something else entirely"), "open")


class TestCrossRefExtraction(unittest.TestCase):

    def test_extracts_mixed_id_types(self) -> None:
        text = "See D-0001, CD-3, BI-2, and L4-01a for context."
        refs = vp.extract_cross_refs(text)
        self.assertEqual(refs, ["D-0001", "CD-3", "BI-2", "L4-01a"])

    def test_deduplicates_preserving_order(self) -> None:
        refs = vp.extract_cross_refs("D-0001 appears twice: D-0001 again.")
        self.assertEqual(refs, ["D-0001"])


class TestRaciExtraction(unittest.TestCase):

    def test_extracts_known_initials_only(self) -> None:
        known = {"AR", "RV"}
        raci = vp.parse_raci_from_text("AR-A ratified after RV-R evaluated. ZZ-C noted.", known, ["AR"])
        self.assertEqual(raci["responsible"], ["RV"])
        self.assertEqual(raci["accountable"], ["AR"])
        self.assertNotIn("consulted", raci)  # ZZ is not a known initial

    def test_falls_back_to_owner_when_no_marker(self) -> None:
        raci = vp.parse_raci_from_text("no markers here", {"AR"}, ["AR"])
        self.assertEqual(raci["responsible"], ["AR"])


class TestTitleExtraction(unittest.TestCase):

    def test_takes_first_sentence(self) -> None:
        title = vp.extract_title("Is this the right approach? Some trailing detail.")
        self.assertEqual(title, "Is this the right approach?")

    def test_truncates_long_questions_without_sentence_break(self) -> None:
        long_q = "a" * 200
        title = vp.extract_title(long_q, max_len=50)
        self.assertLessEqual(len(title), 53)  # allows for the "..." suffix


class TestFormatATableParsing(unittest.TestCase):

    _TABLE = (
        "## Layer 4 — Technical\n\n"
        "| ID | Question | Why It Matters | Owner | Status | Answer |\n"
        "|----|----------|---------------|-------|--------|--------|\n"
        "| D-0010 | Should we do X? | It matters because Y. | AR | 🔴 Open | — |\n"
    )

    def test_parses_single_row(self) -> None:
        import re

        records = vp.parse_format_a_table(
            self._TABLE, layer_id="L4", id_regex=re.compile(r"^D-\d+$"), entry_type="discovery"
        )
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.id, "D-0010")
        self.assertEqual(rec.owner, "AR")
        self.assertEqual(rec.status_raw.strip(), "🔴 Open")


class TestWorkedExample(unittest.TestCase):
    """The ONE worked example: fixtures/taskflow/v1-sample.md -> valid v2 entry."""

    def test_source_fixture_exists(self) -> None:
        self.assertTrue(_DEFAULT_SOURCE.exists(), f"fixture not found: {_DEFAULT_SOURCE}")

    def test_convert_produces_valid_v2_entry(self) -> None:
        fm, body, flags = convert(_DEFAULT_SOURCE, _PEOPLE_YAML)

        self.assertEqual(fm["id"], "D-0003")
        self.assertEqual(fm["type"], "discovery")
        self.assertEqual(fm["layer"], "L4")
        self.assertEqual(fm["status"], "answered")
        self.assertIn("responsible", fm["raci"])

        rendered = render_entry(fm, body)
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "D-0003.md"
            out_path.write_text(rendered, encoding="utf-8")

            schema = load_schema()
            from convert_v1_sample import _load_known_initials  # noqa: PLC0415
            known_initials = _load_known_initials(_PEOPLE_YAML)

            ok, errors = validate_file(out_path, schema, known_initials)
            self.assertTrue(ok, f"converted entry failed validation: {errors}")

    def test_answer_text_preserved_verbatim_not_dropped(self) -> None:
        """Content-fidelity rule: the answer text must survive the conversion."""
        fm, body, flags = convert(_DEFAULT_SOURCE, _PEOPLE_YAML)
        self.assertIn("mergeloom", body)
        self.assertIn("driftset", body)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
