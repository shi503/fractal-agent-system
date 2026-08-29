#!/usr/bin/env python3
"""
Decision Ledger v2 — Worked Import Example

Converts `fixtures/taskflow/v1-sample.md` (a v1-format discovery-log table,
one row) into a valid v2 entry, using the generic helpers in `v1_pattern.py`.

This is the ONE worked example the import pattern ships with. It is not a
general-purpose importer — see `README.md` in this directory for what a
project-specific adapter needs to add (table-format detection, an
owner-name lookup, etc.) to import a full corpus.

Usage:
    python3 tools/decision-ledger/import-pattern/convert_v1_sample.py
    python3 tools/decision-ledger/import-pattern/convert_v1_sample.py --out /tmp/D-0003-imported.md

Exit codes: 0 = converted and validated clean; 1 = conversion or validation error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_IMPORT_PATTERN_DIR = Path(__file__).resolve().parent
_DL_ROOT = _IMPORT_PATTERN_DIR.parent
_STORAGE_DIR = _DL_ROOT / "storage"
_SCHEMA_DIR = _DL_ROOT / "schema"
_REPO_ROOT = _IMPORT_PATTERN_DIR.parents[2]

for _d in (_IMPORT_PATTERN_DIR, _STORAGE_DIR, _SCHEMA_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from v1_pattern import D_ID_RE, parse_format_a_table, transform_record  # noqa: E402
from frontmatter import render_entry  # noqa: E402
from validate import load_schema, validate_file  # noqa: E402

_DEFAULT_SOURCE = _REPO_ROOT / "fixtures" / "taskflow" / "v1-sample.md"
_PEOPLE_YAML = _REPO_ROOT / "fixtures" / "taskflow" / "people.yaml"

_D_ID_TABLE_RE = re.compile(r"^D-\d{1,4}[a-z]?$")


def _load_known_initials(people_yaml_path: Path) -> set[str]:
    """Extract the set of known initials from a people.yaml-shaped file."""
    text = people_yaml_path.read_text(encoding="utf-8")
    initials: set[str] = set()
    in_people = False
    for line in text.splitlines():
        if re.match(r"^people:", line):
            in_people = True
            continue
        if in_people:
            m = re.match(r"^  ([A-Z]{2,4}):", line)
            if m:
                initials.add(m.group(1))
            elif line and not line.startswith(" ") and not line.startswith("#"):
                in_people = False
    return initials


def _extract_layer_section(text: str, heading: str) -> str:
    """Return the text of a `## <heading>` section, up to the next `## ` heading."""
    start = text.find(f"## {heading}")
    if start == -1:
        raise ValueError(f"section '## {heading}' not found in source")
    rest = text[start:]
    next_heading = re.search(r"\n## ", rest[1:])
    end = next_heading.start() + 1 if next_heading else len(rest)
    return rest[:end]


def convert(source_path: Path, people_yaml_path: Path) -> tuple[dict, str, list[str]]:
    """Convert the single v1 table row in *source_path* into a v2 (frontmatter, body, flags)."""
    text = source_path.read_text(encoding="utf-8")
    section = _extract_layer_section(text, "Layer 4 — Technical")

    records = parse_format_a_table(
        section,
        layer_id="L4",
        id_regex=_D_ID_TABLE_RE,
        entry_type="discovery",
    )
    if not records:
        raise ValueError("no D-item rows found in the Layer 4 — Technical table")
    record = records[0]

    known_initials = _load_known_initials(people_yaml_path)
    fm, body, flags = transform_record(
        record,
        known_initials=known_initials,
        default_created="2026-08-12T00:00:00Z",
        default_updated="2026-08-17T00:00:00Z",
    )
    return fm, body, flags


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=_DEFAULT_SOURCE, help="v1-format source file")
    p.add_argument("--people", type=Path, default=_PEOPLE_YAML, help="people registry to resolve initials against")
    p.add_argument("--out", type=Path, default=None, help="write the converted entry here (default: stdout only)")
    args = p.parse_args(argv)

    try:
        fm, body, flags = convert(args.source, args.people)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = render_entry(fm, body)

    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
        target = args.out
    else:
        import tempfile

        tmp = Path(tempfile.mkstemp(suffix=".md")[1])
        tmp.write_text(rendered, encoding="utf-8")
        target = tmp

    schema = load_schema()
    known_initials = _load_known_initials(args.people)
    ok, errors = validate_file(target, schema, known_initials)

    print(rendered)
    print("---", file=sys.stderr)
    if flags:
        print(f"Import flags: {flags}", file=sys.stderr)
    if ok:
        print(f"VALID — converted entry passes schema validation ({fm['id']})", file=sys.stderr)
    else:
        print(f"INVALID — {errors}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
