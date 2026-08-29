#!/usr/bin/env python3
"""
Decision Ledger v2 — Entry Validator
Usage: python3 validate.py <directory-of-md-files>

Validates YAML frontmatter in every .md file against schema.yaml and people.yaml.
Reports per-file pass/fail with line-precise error messages.
Exit code: 0 if all pass, 1 if any fail.

Language choice: Python 3.12 (stdlib only — no pip install required).
A standalone Python script avoids tying schema validation to any particular
JS/TS toolchain that other parts of the repo might use. See README.md for
rationale.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (stdlib only — no PyYAML required)
# Supports the subset of YAML used in decision-ledger frontmatter:
#   scalar strings/ints, lists, nested mappings (one level deep).
# Falls back gracefully on unsupported constructs.
# ---------------------------------------------------------------------------


def _parse_value(raw: str) -> Any:
    """Parse a scalar YAML value."""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.lower() in ("true",):
        return True
    if raw.lower() in ("false",):
        return False
    if raw.lower() in ("null", "~", ""):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_inline_list(raw: str) -> list[Any]:
    """Parse an inline YAML list: [a, b, c] or ["x", "y"]."""
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    items = []
    for item in inner.split(","):
        items.append(_parse_value(item))
    return [i for i in items if i is not None]


def parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    """
    Extract YAML frontmatter from a markdown file.
    Returns (frontmatter_dict, error_list).
    error_list is empty on success; contains messages otherwise.
    Line numbers in errors are 1-based relative to the frontmatter block.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["line 1: file does not begin with YAML frontmatter delimiter '---'"]

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return {}, ["line 1: YAML frontmatter not closed (missing closing '---')"]

    fm_lines = lines[1:end]
    errors: list[str] = []
    result: dict[str, Any] = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        lineno = i + 2  # +1 for 0-index, +1 for opening ---
        stripped = line.rstrip()

        # Skip blank or comment lines
        if not stripped or stripped.lstrip().startswith("#"):
            i += 1
            continue

        # Top-level key: value
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', stripped)
        if not m:
            errors.append(f"line {lineno}: cannot parse: {stripped!r}")
            i += 1
            continue

        key = m.group(1)
        val_raw = m.group(2).strip()

        # Inline list
        if val_raw.startswith("["):
            result[key] = _parse_inline_list(val_raw)
            i += 1
            continue

        # Empty value — may be followed by nested mapping or block list
        if not val_raw:
            nested: dict[str, Any] = {}
            block_list: list[Any] = []
            i += 1
            while i < len(fm_lines):
                sub = fm_lines[i]
                sub_stripped = sub.rstrip()
                if not sub_stripped:
                    i += 1
                    break
                indent = len(sub) - len(sub.lstrip())
                if indent == 0:
                    break
                # Block list item
                lm = re.match(r'^\s+-\s+(.*)', sub_stripped)
                if lm:
                    block_list.append(_parse_value(lm.group(1)))
                    i += 1
                    continue
                # Nested mapping
                nm = re.match(r'^\s+([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', sub_stripped)
                if nm:
                    nkey = nm.group(1)
                    nval_raw = nm.group(2).strip()
                    if nval_raw.startswith("["):
                        nested[nkey] = _parse_inline_list(nval_raw)
                    elif not nval_raw:
                        nested[nkey] = None
                    else:
                        nested[nkey] = _parse_value(nval_raw)
                    i += 1
                    continue
                i += 1
                break
            if block_list:
                result[key] = block_list
            elif nested:
                result[key] = nested
            else:
                result[key] = None
            continue

        result[key] = _parse_value(val_raw)
        i += 1

    return result, errors


# ---------------------------------------------------------------------------
# Schema + people loader
# ---------------------------------------------------------------------------

SCHEMA_DIR = Path(__file__).parent


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """
    Load a simple YAML file (used for schema.yaml and people.yaml).
    Uses the same minimal parser — sufficient for our schema files.
    """
    text = path.read_text(encoding="utf-8")
    data, errors = parse_frontmatter("---\n" + text + "\n---")
    if errors:
        # Fallback: try as plain text key: value
        pass
    return data


def load_schema() -> dict[str, Any]:
    """Load schema.yaml and return its top-level structure."""
    schema_path = SCHEMA_DIR / "schema.yaml"
    if not schema_path.exists():
        print(f"ERROR: schema.yaml not found at {schema_path}", file=sys.stderr)
        sys.exit(2)
    text = schema_path.read_text(encoding="utf-8")
    return _parse_schema_yaml(text)


def _parse_schema_yaml(text: str) -> dict[str, Any]:
    """Parse schema.yaml to extract allowed values."""
    result: dict[str, Any] = {}

    # Extract allowed_statuses list
    m = re.search(r'allowed_statuses:\s*\n((?:\s+-\s+\S+\n?)+)', text)
    if m:
        result["allowed_statuses"] = [
            re.sub(r'^\s+-\s+', '', line).strip()
            for line in m.group(1).splitlines()
            if re.sub(r'^\s+-\s+', '', line).strip()
        ]

    # Extract allowed_layers list
    m = re.search(r'allowed_layers:\s*\n((?:\s+-\s+\S+\n?)+)', text)
    if m:
        result["allowed_layers"] = [
            re.sub(r'^\s+-\s+', '', line).strip()
            for line in m.group(1).splitlines()
            if re.sub(r'^\s+-\s+', '', line).strip()
        ]

    # Extract entry_types and their id_patterns
    entry_types: dict[str, Any] = {}
    for type_block in re.finditer(
        r'^\s{2}(\w+):\n((?:\s{4}.+\n?)*)', text, re.MULTILINE
    ):
        type_name = type_block.group(1)
        block = type_block.group(2)
        # Only process if it looks like an entry_type (has id_pattern)
        id_m = re.search(r'id_pattern:\s*"([^"]+)"', block)
        req_m = re.search(r'required_fields:\s*\n((?:\s{6}-\s+\S+\n?)+)', block)
        if id_m:
            required = []
            if req_m:
                required = [
                    re.sub(r'^\s+-\s+', '', ln).strip()
                    for ln in req_m.group(1).splitlines()
                    if re.sub(r'^\s+-\s+', '', ln).strip()
                ]
            entry_types[type_name] = {
                "id_pattern": id_m.group(1),
                "required_fields": required,
            }

    result["entry_types"] = entry_types

    # Extract iso8601 pattern from field_types
    m = re.search(r'iso8601_datetime:\s*\n.*?pattern:\s*"([^"]+)"', text, re.DOTALL)
    if m:
        result["iso8601_pattern"] = m.group(1)

    # Extract initials pattern
    m = re.search(r'\binitials:\s*\n.*?pattern:\s*"([^"]+)"', text, re.DOTALL)
    if m:
        result["initials_pattern"] = m.group(1)

    return result


def load_people() -> set[str]:
    """Load people.yaml and return the set of known initials.

    Resolution order:
      1. $DL_PEOPLE_PATH, if set — lets a caller point at a project-specific
         people registry without editing this file.
      2. tools/decision-ledger/schema/people.yaml (the default registry
         shipped alongside the validator).
    """
    import os

    override = os.environ.get("DL_PEOPLE_PATH", "").strip()
    override_path = Path(override) if override else None
    fallback_path = SCHEMA_DIR / "people.yaml"

    if override_path and override_path.exists():
        people_path = override_path
    elif fallback_path.exists():
        people_path = fallback_path
    else:
        print(
            f"ERROR: people.yaml not found at {override_path} or {fallback_path}",
            file=sys.stderr,
        )
        sys.exit(2)
    text = people_path.read_text(encoding="utf-8")
    # Extract initials: keys directly under `people:` that are 2-4 uppercase letters
    initials: set[str] = set()
    in_people = False
    for line in text.splitlines():
        if re.match(r'^people:', line):
            in_people = True
            continue
        if in_people:
            m = re.match(r'^  ([A-Z]{2,4}):', line)
            if m:
                initials.add(m.group(1))
            elif line and not line.startswith(" ") and not line.startswith("#"):
                in_people = False
    return initials


# ---------------------------------------------------------------------------
# Validation engine
# ---------------------------------------------------------------------------

ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$"
)
INITIALS_RE = re.compile(r"^[A-Z]{2,4}$")

# Map type field value → entry_types key
TYPE_ALIASES: dict[str, str] = {
    "discovery": "discovery",
    "critical_decision": "critical_decision",
    "big_idea": "big_idea",
    "layer_item": "layer_item",
}


def validate_entry(
    fm: dict[str, Any],
    schema: dict[str, Any],
    known_initials: set[str],
    filename: str,
) -> list[str]:
    """
    Validate a parsed frontmatter dict against the schema.
    Returns a list of error strings. Empty list = pass.
    """
    errors: list[str] = []

    # --- type field ---
    raw_type = fm.get("type")
    if not raw_type:
        errors.append("frontmatter missing required field: type")
        return errors

    entry_type_key = TYPE_ALIASES.get(str(raw_type))
    if entry_type_key is None:
        allowed = list(TYPE_ALIASES.keys())
        errors.append(
            f"field 'type': unknown value {raw_type!r}; allowed: {allowed}"
        )
        return errors

    type_cfg = schema.get("entry_types", {}).get(entry_type_key, {})

    # --- id field ---
    entry_id = fm.get("id")
    if not entry_id:
        errors.append("frontmatter missing required field: id")
    else:
        id_pattern = type_cfg.get("id_pattern")
        if id_pattern and not re.match(id_pattern, str(entry_id)):
            errors.append(
                f"field 'id': value {entry_id!r} does not match pattern {id_pattern!r} for type {raw_type!r}"
            )

    # --- required fields ---
    required = type_cfg.get("required_fields", [])
    for field in required:
        if field not in fm or fm[field] is None:
            errors.append(f"frontmatter missing required field: {field}")

    if errors:
        return errors

    # --- status ---
    status = fm.get("status")
    allowed_statuses = schema.get("allowed_statuses", [])
    if allowed_statuses and status not in allowed_statuses:
        errors.append(
            f"field 'status': value {status!r} not in allowed set {allowed_statuses}"
        )

    # --- layer (required for layer_item, optional for others) ---
    layer = fm.get("layer")
    if raw_type == "layer_item" and not layer:
        errors.append("field 'layer': required for entry type 'layer_item'")
    if layer:
        allowed_layers = schema.get("allowed_layers", [])
        if allowed_layers and layer not in allowed_layers:
            errors.append(
                f"field 'layer': value {layer!r} not in allowed set {allowed_layers}"
            )

    # --- RACI ---
    raci = fm.get("raci")
    if not isinstance(raci, dict):
        errors.append("field 'raci': must be a mapping with at least 'responsible'")
    else:
        responsible = raci.get("responsible")
        if not responsible:
            errors.append(
                "field 'raci.responsible': must be non-empty (FM-4: every entry must have an owner)"
            )
        else:
            if isinstance(responsible, str):
                responsible = [responsible]
            for init in responsible:
                _check_initials(init, "raci.responsible", known_initials, errors)

        for role in ("accountable", "consulted", "informed"):
            members = raci.get(role)
            if members:
                if isinstance(members, str):
                    members = [members]
                for init in members:
                    _check_initials(init, f"raci.{role}", known_initials, errors)

    # --- audit fields ---
    for ts_field in ("created", "updated"):
        val = fm.get(ts_field)
        if val and not ISO8601_RE.match(str(val)):
            errors.append(
                f"field '{ts_field}': value {val!r} is not a valid ISO-8601 datetime "
                f"(expected format: 2026-04-22T14:31:00Z)"
            )

    for actor_field in ("created_by", "updated_by"):
        val = fm.get(actor_field)
        if val:
            _check_initials(str(val), actor_field, known_initials, errors)

    return errors


def _check_initials(
    init: str,
    field: str,
    known_initials: set[str],
    errors: list[str],
) -> None:
    init = init.strip()
    if not INITIALS_RE.match(init):
        errors.append(
            f"field '{field}': {init!r} is not valid initials (must be 2-4 uppercase letters)"
        )
    elif init not in known_initials:
        errors.append(
            f"field '{field}': initials {init!r} not found in people.yaml "
            f"(known: {sorted(known_initials)})"
        )


# ---------------------------------------------------------------------------
# Per-file driver
# ---------------------------------------------------------------------------


def validate_file(
    path: Path,
    schema: dict[str, Any],
    known_initials: set[str],
) -> tuple[bool, list[str]]:
    """
    Validate a single .md file.
    Returns (passed: bool, errors: list[str]) where errors are human-readable,
    each prefixed with the filename and a line number where determinable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, [f"cannot read file: {exc}"]

    fm, parse_errors = parse_frontmatter(text)
    if parse_errors:
        return False, [f"{path.name}:{e}" for e in parse_errors]

    validate_errors = validate_entry(fm, schema, known_initials, path.name)
    if validate_errors:
        # Attempt to annotate errors with approximate line numbers by scanning
        # frontmatter for the field name
        annotated = []
        lines = text.splitlines()
        for err in validate_errors:
            # Extract the field name if present (e.g., "field 'status':")
            fm_field_m = re.match(r"field '([^']+)'", err)
            lineno = None
            if fm_field_m:
                field_name = fm_field_m.group(1).split(".")[0]
                for i, line in enumerate(lines[1:], start=2):
                    if line.strip() == "---":
                        break
                    if re.match(rf"^{re.escape(field_name)}\s*:", line):
                        lineno = i
                        break
            prefix = f"{path.name}:{lineno}" if lineno else f"{path.name}"
            annotated.append(f"{prefix}: {err}")
        return False, annotated

    return True, []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 validate.py <directory>", file=sys.stderr)
        print("       Validates all .md files in the given directory.", file=sys.stderr)
        return 2

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"ERROR: path does not exist: {target}", file=sys.stderr)
        return 2

    schema = load_schema()
    known_initials = load_people()

    if target.is_file():
        md_files = [target] if target.suffix == ".md" else []
    else:
        md_files = sorted(target.rglob("*.md"))

    if not md_files:
        print(f"No .md files found in {target}")
        return 0

    passed = 0
    failed = 0
    all_errors: list[str] = []

    for md_file in md_files:
        ok, errors = validate_file(md_file, schema, known_initials)
        if ok:
            passed += 1
            print(f"  PASS  {md_file}")
        else:
            failed += 1
            print(f"  FAIL  {md_file}")
            for err in errors:
                print(f"        {err}")
            all_errors.extend(errors)

    total = passed + failed
    print(f"\n{passed}/{total} files passed validation.")
    if failed:
        print(f"{failed} file(s) failed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
