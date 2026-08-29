"""
Decision Ledger v2 — Frontmatter Parser / Serialiser

Parses and round-trips YAML frontmatter in markdown files.
Uses only Python stdlib — no PyYAML, no external dependencies.

The parser handles the subset of YAML present in decision-ledger entries:
  - Scalar strings, integers, booleans, null
  - Inline lists: [A, B, C]
  - Block lists (dash-indented)
  - Nested mappings (one level deep: raci: { responsible: [...] })

Serialiser emits a deterministic, human-readable YAML block.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Frontmatter parser (imported from schema/validate.py, deduplicated here)
# ---------------------------------------------------------------------------

def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
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
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    items = []
    for item in inner.split(","):
        v = _parse_value(item)
        if v is not None:
            items.append(v)
    return items


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """
    Parse a markdown file.

    Returns:
        (frontmatter_dict, body_text, error_list)

    *body_text* is everything after the closing '---' delimiter.
    *error_list* is empty on success.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text, ["line 1: file does not begin with YAML frontmatter '---'"]

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, text, ["YAML frontmatter not closed (missing closing '---')"]

    fm_lines = [ln.rstrip("\n").rstrip("\r") for ln in lines[1:end_idx]]
    body = "".join(lines[end_idx + 1:])

    errors: list[str] = []
    result: dict[str, Any] = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        lineno = i + 2
        stripped = line.rstrip()

        if not stripped or stripped.lstrip().startswith("#"):
            i += 1
            continue

        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', stripped)
        if not m:
            errors.append(f"line {lineno}: cannot parse: {stripped!r}")
            i += 1
            continue

        key = m.group(1)
        val_raw = m.group(2).strip()

        if val_raw.startswith("["):
            result[key] = _parse_inline_list(val_raw)
            i += 1
            continue

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
                lm = re.match(r'^\s+-\s+(.*)', sub_stripped)
                if lm:
                    block_list.append(_parse_value(lm.group(1)))
                    i += 1
                    continue
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

    return result, body, errors


# ---------------------------------------------------------------------------
# Frontmatter serialiser
# ---------------------------------------------------------------------------

# Canonical field order for deterministic output
_FIELD_ORDER = [
    "id", "type", "layer", "title", "owner", "status",
    "raci", "options", "unlocks", "answer",
    "created", "updated", "created_by", "updated_by",
    "superseded_by", "cross_refs", "tags", "addenda",
]


def _yaml_scalar(value: Any) -> str:
    """Emit a YAML scalar value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    # Quote strings containing special chars
    if any(c in s for c in (':', '#', '[', ']', '{', '}', ',', '&', '*', '!', '|', '>')) or not s:
        return f'"{s}"'
    return s


def _yaml_inline_list(items: list[Any]) -> str:
    return "[" + ", ".join(_yaml_scalar(x) for x in items) + "]"


def serialise_frontmatter(fm: dict[str, Any]) -> str:
    """
    Serialise a frontmatter dict back to a YAML block (without delimiters).
    Output is deterministic: fields follow _FIELD_ORDER; unknown fields appended alphabetically.
    """
    lines: list[str] = []
    emitted: set[str] = set()

    def emit_field(key: str, value: Any) -> None:
        emitted.add(key)
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for subkey, subval in value.items():
                if isinstance(subval, list):
                    lines.append(f"  {subkey}: {_yaml_inline_list(subval)}")
                elif subval is None:
                    lines.append(f"  {subkey}: null")
                else:
                    lines.append(f"  {subkey}: {_yaml_scalar(subval)}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")

    for key in _FIELD_ORDER:
        if key in fm:
            emit_field(key, fm[key])

    for key in sorted(fm.keys()):
        if key not in emitted:
            emit_field(key, fm[key])

    return "\n".join(lines)


def render_entry(fm: dict[str, Any], body: str) -> str:
    """Render a complete markdown file from frontmatter dict + body string."""
    fm_block = serialise_frontmatter(fm)
    body_stripped = body.lstrip("\n")
    return f"---\n{fm_block}\n---\n\n{body_stripped}"
