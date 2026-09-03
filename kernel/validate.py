#!/usr/bin/env python3
"""Validate the kernel example BLUEPRINT and enforce the portable contract.

Not a router. Checks:
  1. Example BLUEPRINT matches schemas/blueprint.schema.json
  2. Graph law: depends_on ids exist, no cycles, parallel ids exist,
     prd path matches workstream id
  3. schemas/, templates/, and examples/ contain no installer paths
     and no model-tier field
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write(
        "Missing deps. Install with: python3 -m pip install pyyaml jsonschema\n"
    )
    sys.exit(2)

KERNEL = Path(__file__).resolve().parent
SCHEMA_PATH = KERNEL / "schemas" / "blueprint.schema.json"
EXAMPLE_PATH = (
    KERNEL
    / "examples"
    / "nova-p1-notification-core"
    / "BLUEPRINT-NOVA-P1-NotificationCore.yaml"
)
SCAN_ROOTS = [KERNEL / "schemas", KERNEL / "templates", KERNEL / "examples"]

# Installer leaks that must not appear in kernel schemas, templates, or examples.
FORBIDDEN = [
    (re.compile(r"\.claude/"), ".claude/ path"),
    (re.compile(r"(?m)^model\s*:"), "model: field"),
    (re.compile(r"model:\s*(opus|sonnet|haiku)"), "model: opus|sonnet|haiku"),
]


def fail(message: str) -> None:
    sys.stderr.write(f"kernel/validate.py: {message}\n")
    sys.exit(1)


def _stringify_dates(value):
    """Keep ISO dates as strings so they match the schema (PyYAML may parse them)."""
    if hasattr(value, "isoformat") and not isinstance(value, (str, bytes)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _stringify_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify_dates(v) for v in value]
    return value


def load_blueprint() -> dict:
    raw = EXAMPLE_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        fail(f"{EXAMPLE_PATH.name} must be a YAML object, not {type(data).__name__}")
    return _stringify_dates(data)


def validate_schema(blueprint: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(blueprint), key=lambda e: list(e.path))
    if errors:
        lines = [f"{EXAMPLE_PATH} failed schema validation:"]
        for err in errors:
            loc = "/".join(str(p) for p in err.path) or "(root)"
            lines.append(f"  - {loc}: {err.message}")
        fail("\n".join(lines))


def validate_graph(blueprint: dict) -> None:
    workstreams = blueprint["workstreams"]
    ids = [ws["id"] for ws in workstreams]
    if len(ids) != len(set(ids)):
        fail(f"duplicate workstream ids: {ids}")

    id_set = set(ids)
    by_id = {ws["id"]: ws for ws in workstreams}

    for ws in workstreams:
        wid = ws["id"]
        expected_prd = f"workstreams/{wid}/prd-{wid}.md"
        if ws["prd"] != expected_prd:
            fail(f"{wid}: prd must be {expected_prd}, got {ws['prd']}")
        for dep in ws["depends_on"]:
            if dep not in id_set:
                fail(f"{wid}: depends_on unknown id {dep!r}")
            if dep == wid:
                fail(f"{wid}: depends_on cannot include itself")

    # Cycle check (Kahn).
    remaining = {wid: set(by_id[wid]["depends_on"]) for wid in ids}
    ready = [wid for wid, deps in remaining.items() if not deps]
    seen = []
    while ready:
        current = ready.pop()
        seen.append(current)
        for wid, deps in remaining.items():
            if current in deps:
                deps.remove(current)
                if not deps and wid not in seen and wid not in ready:
                    ready.append(wid)
    if len(seen) != len(ids):
        cyclic = sorted(id_set - set(seen))
        fail(f"depends_on cycle involving: {cyclic}")

    for i, wave in enumerate(blueprint["parallel"]):
        for wid in wave:
            if wid not in id_set:
                fail(f"parallel wave {i}: unknown id {wid!r}")

    missing_prd = []
    example_root = EXAMPLE_PATH.parent
    for ws in workstreams:
        prd_path = example_root / ws["prd"]
        if not prd_path.is_file():
            missing_prd.append(str(prd_path.relative_to(KERNEL.parent)))
    if missing_prd:
        fail("PRD files missing:\n  - " + "\n  - ".join(missing_prd))


def scan_installer_leaks() -> None:
    hits = []
    for root in SCAN_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".json", ".yaml", ".yml", ".md"}:
                continue
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(KERNEL.parent)
            for pattern, label in FORBIDDEN:
                if pattern.search(text):
                    hits.append(f"{rel}: {label}")
    if hits:
        fail("installer leak in kernel schemas/templates/examples:\n  - " + "\n  - ".join(hits))


def main() -> None:
    if not EXAMPLE_PATH.is_file():
        fail(f"missing example BLUEPRINT: {EXAMPLE_PATH}")
    blueprint = load_blueprint()
    validate_schema(blueprint)
    validate_graph(blueprint)
    scan_installer_leaks()
    print(f"OK  {EXAMPLE_PATH.relative_to(KERNEL.parent)} matches blueprint.schema.json")
    print("OK  graph law (depends_on ids, acyclic, parallel, PRD paths)")
    print("OK  no installer leaks in schemas/templates/examples")


if __name__ == "__main__":
    main()
