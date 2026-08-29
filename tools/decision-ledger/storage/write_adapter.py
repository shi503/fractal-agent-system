#!/usr/bin/env python3
"""
Decision Ledger v2 — Write Adapter

Thin helper for scripted/agent callers that need the full atomic write sequence
in one shot: lock -> validate -> write -> sensitive-data lint -> unlock.

Usage:
    python3 tools/decision-ledger/storage/write_adapter.py \\
        --store <dl-root> \\
        --id <ENTRY-ID> \\
        --actor <INITIALS> \\
        --body-file <path-to-body.txt> \\
        [--set key=value ...]

Exit codes:
    0 — success; entry written, validated, lint-clean, committed (git add only)
    1 — validation error (entry NOT committed)
    2 — sensitive-data lint blocked (entry NOT committed)
    3 — lock conflict (entry NOT written)
    4 — usage/runtime error

Printed JSON to stdout on success:
    {"status": "ok", "id": "D-NNN", "hash": "<sha256-prefix>"}

On error:
    {"status": "error", "code": N, "message": "..."}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_STORAGE_DIR = Path(__file__).parent
_SCHEMA_DIR = _STORAGE_DIR.parent / "schema"

sys.path.insert(0, str(_STORAGE_DIR))
sys.path.insert(0, str(_SCHEMA_DIR))

from store import DecisionStore  # noqa: E402
from validate import load_schema, load_people, validate_file  # noqa: E402


# ---------------------------------------------------------------------------
# Sensitive-data pattern guard
#
# A conservative, project-agnostic lint that blocks the write if the entry
# body looks like it embeds secrets or personally identifying record numbers.
# Projects with stricter compliance needs (health data, financial records,
# etc.) should extend _SENSITIVE_PATTERNS for their own domain.
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS = [
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),                       # SSN-shaped
    re.compile(r'\b(api[_-]?key|secret|token)\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'),  # JWT-shaped
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
]


def _sensitive_scan(path: Path) -> list[str]:
    """Return list of sensitive-pattern match descriptions found in *path*. Empty = clean."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    matches: list[str] = []
    for pat in _SENSITIVE_PATTERNS:
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------

def _result(status: str, **kwargs: object) -> None:
    print(json.dumps({"status": status, **kwargs}))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="write_adapter",
        description="Scripted atomic write helper: lock -> validate -> write -> lint -> unlock",
    )
    p.add_argument("--store", type=Path, required=True, help="Decision-log root directory")
    p.add_argument("--id", required=True, help="Entry ID (e.g. D-NNN, CD-N, BI-NN, L4-07)")
    p.add_argument("--actor", required=True, help="Author initials (must be in people.yaml)")
    p.add_argument(
        "--body-file",
        type=Path,
        default=None,
        help="Path to a file containing the markdown body text",
    )
    p.add_argument(
        "--body",
        default=None,
        help="Inline body text (alternative to --body-file)",
    )
    p.add_argument(
        "--set",
        action="append",
        metavar="KEY=VALUE",
        dest="sets",
        default=[],
        help="Frontmatter field patch (repeatable). For nested raci use --raci-* flags.",
    )
    # RACI helpers — assemble into a dict before writing
    p.add_argument("--raci-responsible", default=None, help="Comma-separated initials for raci.responsible")
    p.add_argument("--raci-accountable", default=None, help="Comma-separated initials for raci.accountable")
    p.add_argument("--raci-consulted", default=None, help="Comma-separated initials for raci.consulted")
    p.add_argument("--raci-informed", default=None, help="Comma-separated initials for raci.informed")
    p.add_argument(
        "--no-lock",
        action="store_true",
        help="Skip the lock step (use only when caller already holds the lock)",
    )
    args = p.parse_args(argv)

    store_root = args.store.resolve()
    entry_id: str = args.id
    actor: str = args.actor

    # Body
    if args.body_file:
        try:
            body = args.body_file.read_text(encoding="utf-8")
        except OSError as exc:
            _result("error", code=4, message=f"cannot read body-file: {exc}")
            return 4
    elif args.body is not None:
        body = args.body
    else:
        body = None  # preserve existing body

    # Frontmatter patches (scalar fields)
    patches: dict[str, object] = {}
    for kv in (args.sets or []):
        if "=" not in kv:
            _result("error", code=4, message=f"--set requires KEY=VALUE, got: {kv!r}")
            return 4
        k, _, v = kv.partition("=")
        patches[k.strip()] = v.strip()

    # RACI dict (assembled from --raci-* flags)
    raci: dict[str, list[str]] = {}
    if args.raci_responsible:
        raci["responsible"] = [s.strip() for s in args.raci_responsible.split(",")]
    if args.raci_accountable:
        raci["accountable"] = [s.strip() for s in args.raci_accountable.split(",")]
    if args.raci_consulted:
        raci["consulted"] = [s.strip() for s in args.raci_consulted.split(",")]
    if args.raci_informed:
        raci["informed"] = [s.strip() for s in args.raci_informed.split(",")]
    if raci:
        patches["raci"] = raci

    store = DecisionStore(store_root)
    try:
        # Step 1: Lock
        if not args.no_lock:
            acquired = store.lock(entry_id, actor)
            if not acquired:
                lock_info = store.get_lock(entry_id)
                if lock_info:
                    held_by = lock_info.get("actor", "unknown")
                    expires = lock_info.get("expires_at", "unknown")
                    _result(
                        "error",
                        code=3,
                        message=f"Entry {entry_id} is locked by {held_by} until {expires}",
                        lock_actor=held_by,
                        lock_expires=expires,
                    )
                else:
                    _result("error", code=3, message=f"Entry {entry_id} lock acquisition failed")
                return 3

        # Step 2: Load existing entry (or create skeleton)
        try:
            fm, existing_body = store.read(entry_id)
        except FileNotFoundError:
            fm = {"id": entry_id}
            existing_body = ""

        # Apply frontmatter patches
        for k, v in patches.items():
            fm[k] = v

        # Ensure required audit fields have defaults if creating new
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if "created" not in fm or not fm["created"]:
            fm["created"] = now_iso
        if "created_by" not in fm or not fm["created_by"]:
            fm["created_by"] = actor
        fm["updated"] = patches.get("updated", now_iso)
        fm["updated_by"] = actor

        resolved_body = body if body is not None else existing_body

        # Step 3: Write
        try:
            after_hash = store.write(entry_id, fm, resolved_body, actor)
        except PermissionError as exc:
            _result("error", code=3, message=str(exc))
            return 3
        except ValueError as exc:
            _result("error", code=1, message=f"write error: {exc}")
            return 1

        entry_path = store.root / f"{entry_id}.md"

        # Step 4: Validate against schema.yaml + people.yaml
        schema = load_schema()
        known_initials = load_people()
        ok, validate_errors = validate_file(entry_path, schema, known_initials)
        if not ok:
            _result(
                "error",
                code=1,
                message="Schema validation failed",
                errors=validate_errors,
            )
            return 1

        # Step 5: Sensitive-data lint
        sensitive_matches = _sensitive_scan(entry_path)
        if sensitive_matches:
            _result(
                "error",
                code=2,
                message="Sensitive-data lint blocked — entry contains a flagged pattern",
                matches=sensitive_matches,
            )
            return 2

        # Step 6: Release lock
        if not args.no_lock:
            store.unlock(entry_id, actor)

        _result("ok", id=entry_id, hash=after_hash[:12])
        return 0

    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
