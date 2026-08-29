#!/usr/bin/env python3
"""
Decision Ledger v2 — Schema Examples Round-Trip Test

`schema-examples.md` documents one fully-populated example per entry type as
a fenced ```yaml block (frontmatter + body together, exactly as a canonical
.md entry would look). This test extracts each block and runs it through the
same validator used for real entries, so the documentation stays correct —
a broken example fails CI here instead of silently rotting in the docs.
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

_SCHEMA_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCHEMA_DIR))

from validate import load_schema, load_people, validate_file  # noqa: E402

_EXAMPLES_MD = _SCHEMA_DIR / "schema-examples.md"
_YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _extract_examples() -> list[str]:
    text = _EXAMPLES_MD.read_text(encoding="utf-8")
    return _YAML_BLOCK_RE.findall(text)


class TestSchemaExamplesRoundTrip(unittest.TestCase):

    def test_examples_file_has_four_blocks(self) -> None:
        blocks = _extract_examples()
        self.assertEqual(len(blocks), 4, "Expected one example per entry type")

    def test_each_example_validates(self) -> None:
        schema = load_schema()
        known_initials = load_people()
        blocks = _extract_examples()
        self.assertTrue(blocks, "No examples extracted from schema-examples.md")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for i, block in enumerate(blocks):
                entry_path = tmp_path / f"example-{i}.md"
                entry_path.write_text(block.strip() + "\n", encoding="utf-8")
                with self.subTest(example=i):
                    ok, errors = validate_file(entry_path, schema, known_initials)
                    self.assertTrue(ok, f"Example {i} failed validation: {errors}")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
