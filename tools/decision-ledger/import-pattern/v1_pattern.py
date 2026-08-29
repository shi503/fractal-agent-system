"""
Decision Ledger v2 — v1-table Import Pattern (generic, reusable helpers)

This module carries the *reusable pattern* for importing a legacy discovery
log kept as markdown tables into Decision Ledger v2 entries. It intentionally
does NOT encode any one project's table layout, owner-name conventions, or
organisational RACI defaults — those are project-specific and belong in a
thin adapter script that imports from here (see `convert_v1_sample.py` for a
worked example against the TaskFlow fixture corpus).

What's generic and lives here:
  - Status emoji <-> v2 status string mapping
  - Cross-reference ID extraction (D-/CD-/BI-/L#- patterns)
  - A markdown-table-row splitter tolerant of "Format A" tables:
      | ID | Question | Why It Matters | Owner | Status | Answer |
  - RACI-suffix extraction from free text (`XX-R`, `XX-A`, ...), parameterised
    by a caller-supplied set of known initials rather than a hardcoded org chart
  - Title extraction (first sentence / natural break from a question column)
  - Date extraction from free text
  - Body assembly (## Context / ## Answer / ## Unmapped Fields)

What's deliberately NOT here (out of scope for this port — carry the pattern,
not one project's parsing rules):
  - "Format B" compact tables with inline emoji-embedded answers
  - Any owner-name -> initials lookup table (organisation-specific)
  - Activity-log date backfill from a second source document
  - A full-corpus batch-import CLI

Language: Python 3.9+ stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------

EMOJI_STATUS_MAP: dict[str, str] = {
    "🟢": "answered",
    "🔴": "open",
    "🟡": "in_discovery",
    "🔶": "conflicted",
    "🔵": "pending_signoff",
    "⚫": "deferred",
    "⬛": "deferred",
}

STATUS_TEXT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Answered", re.IGNORECASE), "answered"),
    (re.compile(r"In Discovery", re.IGNORECASE), "in_discovery"),
    (re.compile(r"Pending Sign.?off", re.IGNORECASE), "pending_signoff"),
    (re.compile(r"Conflicted", re.IGNORECASE), "conflicted"),
    (re.compile(r"Deferred|Closed", re.IGNORECASE), "deferred"),
    (re.compile(r"Open\b", re.IGNORECASE), "open"),
]


def parse_status(raw: str) -> str:
    """Map a raw v1 status cell (emoji and/or text) to a v2 status string."""
    for emoji, status in EMOJI_STATUS_MAP.items():
        if emoji in raw:
            return status
    for pat, status in STATUS_TEXT_PATTERNS:
        if pat.search(raw):
            return status
    return "open"


# ---------------------------------------------------------------------------
# Cross-reference ID extraction
# ---------------------------------------------------------------------------

D_ID_RE = re.compile(r"\bD-(\d{1,4}[a-z]?)\b")
CD_ID_RE = re.compile(r"\bCD-(\d{1,3})\b")
BI_ID_RE = re.compile(r"\bBI-(\d{1,3})\b")
L_ID_RE = re.compile(r"\bL(\d{1,2})-(\d{1,2}[a-z]?)\b")


def extract_cross_refs(text: str) -> list[str]:
    """Extract all referenced entry IDs from a text blob, order-preserving."""
    refs: list[str] = []
    for m in D_ID_RE.finditer(text):
        refs.append(f"D-{m.group(1)}")
    for m in CD_ID_RE.finditer(text):
        refs.append(f"CD-{m.group(1)}")
    for m in BI_ID_RE.finditer(text):
        refs.append(f"BI-{m.group(1)}")
    for m in L_ID_RE.finditer(text):
        refs.append(f"L{m.group(1)}-{m.group(2)}")
    seen: set[str] = set()
    unique: list[str] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------

def split_md_table_row(line: str) -> list[str]:
    """Split a markdown table row on `|`. Sufficient for tables whose only
    embedded `|` characters (if any) live in the final column."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip() for c in stripped.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    """True for a markdown table separator row (the `---|---|---` line)."""
    return all(re.match(r"^[-: ]+$", c) for c in cells if c)


def normalize_id_cell(raw_id: str) -> str:
    """Strip bold markers and whitespace from an ID cell."""
    return re.sub(r"\*\*", "", raw_id).strip()


@dataclass
class V1Record:
    """One row parsed from a "Format A" v1 table:
    | ID | Question | Why It Matters | Owner | Status | Answer |
    """

    id: str
    entry_type: str
    layer: str | None
    question: str
    why_it_matters: str
    owner: str
    status_raw: str
    answer: str
    cross_refs: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def parse_format_a_table(
    text: str,
    layer_id: str | None,
    id_regex: re.Pattern[str],
    entry_type: str,
) -> list[V1Record]:
    """
    Parse "Format A" table rows: `| ID | Question | Why It Matters | Owner | Status | Answer |`.

    *id_regex* determines which ID prefix this table holds (e.g. `^D-\\d{1,4}[a-z]?$`).
    Rows whose ID cell doesn't match are skipped (lets a caller point this at
    a section that contains other content around the table).
    """
    records: list[V1Record] = []
    in_table = False
    past_separator = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = split_md_table_row(line)
        if not cells:
            continue

        if not in_table:
            if "ID" in cells[0] and len(cells) >= 3:
                in_table = True
                past_separator = False
            continue

        if not past_separator:
            if is_separator_row(cells):
                past_separator = True
            continue

        if len(cells) < 3:
            continue

        raw_id = normalize_id_cell(cells[0])
        if not id_regex.match(raw_id):
            continue

        question = cells[1] if len(cells) > 1 else ""
        why = cells[2] if len(cells) > 2 else ""
        owner = cells[3] if len(cells) > 3 else ""
        status_raw = cells[4] if len(cells) > 4 else ""
        answer = "|".join(cells[5:]) if len(cells) > 5 else ""

        cross_refs = [r for r in extract_cross_refs(question + " " + answer) if r != raw_id]

        records.append(
            V1Record(
                id=raw_id,
                entry_type=entry_type,
                layer=layer_id,
                question=question,
                why_it_matters=why,
                owner=owner,
                status_raw=status_raw,
                answer=answer,
                cross_refs=cross_refs,
            )
        )

    return records


# ---------------------------------------------------------------------------
# RACI extraction (parameterised by known initials — no hardcoded org chart)
# ---------------------------------------------------------------------------

RACI_PATTERN = re.compile(r"\b([A-Z]{2,4})-([RACI])\b")


def parse_raci_from_text(
    text: str,
    known_initials: set[str],
    fallback_responsible: list[str],
) -> dict[str, list[str]]:
    """
    Parse RACI assignments (`XX-R`, `XX-A`, `XX-C`, `XX-I`) from free text.

    *known_initials* gates which matches are trusted (a bare two-to-four
    letter uppercase token followed by `-R` is not necessarily a person —
    e.g. it could be a status code — so only tokens present in the caller's
    people registry are accepted).

    Falls back to *fallback_responsible* for `responsible` if no explicit
    `XX-R` marker is found.
    """
    responsible: list[str] = []
    accountable: list[str] = []
    consulted: list[str] = []
    informed: list[str] = []

    for m in RACI_PATTERN.finditer(text):
        initials, role = m.group(1), m.group(2)
        if initials not in known_initials:
            continue
        bucket = {"R": responsible, "A": accountable, "C": consulted, "I": informed}[role]
        if initials not in bucket:
            bucket.append(initials)

    if not responsible:
        responsible = [i for i in fallback_responsible if i in known_initials] or list(fallback_responsible)

    raci: dict[str, list[str]] = {"responsible": responsible}
    if accountable:
        raci["accountable"] = accountable
    if consulted:
        raci["consulted"] = consulted
    if informed:
        raci["informed"] = informed
    return raci


# ---------------------------------------------------------------------------
# Title / date extraction
# ---------------------------------------------------------------------------

def extract_title(question: str, max_len: int = 120) -> str:
    """Extract a title-length fragment from a question/idea column."""
    q = re.sub(r"\*\*", "", question).strip()
    q = re.sub(r"^`[^`]+`\s*", "", q)
    m = re.match(r"^(.{10,%d}?[.?!])\s" % max_len, q)
    if m:
        return m.group(1).strip()
    if len(q) > max_len:
        for sep in (":", " —", " -", ","):
            idx = q.find(sep, 40)
            if 40 < idx < max_len:
                return q[:idx].strip()
        return q[: max_len - 3].strip() + "..."
    return q.strip()


DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def extract_dates(text: str) -> list[str]:
    """Extract YYYY-MM-DD dates found in free text, sorted ascending."""
    return sorted(set(DATE_RE.findall(text)))


def dates_to_iso(dates: list[str], default_created: str, default_updated: str) -> tuple[str, str]:
    """(created, updated) ISO-8601 timestamps derived from a date list, or the
    caller-supplied defaults if no dates were found."""
    if not dates:
        return default_created, default_updated
    return f"{dates[0]}T00:00:00Z", f"{dates[-1]}T00:00:00Z"


# ---------------------------------------------------------------------------
# Body assembly
# ---------------------------------------------------------------------------

def build_body(why_it_matters: str, answer: str, flags: list[str]) -> str:
    """Build the v2 markdown body: ## Context / ## Answer / ## Unmapped Fields."""
    parts: list[str] = []

    if why_it_matters.strip():
        parts += ["## Context", "", why_it_matters.strip(), ""]

    if answer.strip():
        parts += ["## Answer", "", answer.strip(), ""]

    if flags:
        parts += ["## Unmapped Fields", "", "<!-- IMPORT FLAG: review these unmapped values -->"]
        parts += [f"- {f}" for f in flags]
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Top-level transform
# ---------------------------------------------------------------------------

def transform_record(
    record: V1Record,
    known_initials: set[str],
    default_created: str,
    default_updated: str,
) -> tuple[dict[str, Any], str, list[str]]:
    """
    Transform a V1Record into (frontmatter, body, flags).

    Content-fidelity rule: never silently drop answer text or cross-refs.
    Anything that can't be mapped cleanly goes into `flags` and is surfaced
    in the body's `## Unmapped Fields` section and the frontmatter's `addenda`.
    """
    flags: list[str] = list(record.flags)

    owner_clean = record.owner.strip()
    owner_initials = [owner_clean] if re.match(r"^[A-Z]{2,4}$", owner_clean) and owner_clean in known_initials else []
    if not owner_initials:
        found = re.findall(r"\b([A-Z]{2,4})\b", owner_clean)
        owner_initials = [i for i in found if i in known_initials]
    if not owner_initials:
        flags.append(f"FLAG:owner: '{record.owner}' did not resolve to known initials — needs manual review")
        owner_initials = sorted(known_initials)[:1] or ["UNKNOWN"]

    raci_source = record.answer + " " + record.status_raw
    raci = parse_raci_from_text(raci_source, known_initials, owner_initials)

    all_dates = extract_dates(record.answer + " " + record.status_raw)
    created, updated = dates_to_iso(all_dates, default_created, default_updated)

    created_by = raci["responsible"][0] if raci.get("responsible") else owner_initials[0]
    updated_by = created_by

    status = parse_status(record.status_raw)
    title = extract_title(record.question) or record.id

    fm: dict[str, Any] = {
        "id": record.id,
        "type": record.entry_type,
        "title": title,
        "owner": owner_initials[0],
        "status": status,
        "raci": raci,
        "created": created,
        "updated": updated,
        "created_by": created_by,
        "updated_by": updated_by,
    }
    if record.layer:
        fm["layer"] = record.layer
    if record.cross_refs:
        fm["cross_refs"] = record.cross_refs
    if flags:
        fm["addenda"] = [f"[IMPORT] {f}" for f in flags]

    body = build_body(record.why_it_matters, record.answer, flags)
    return fm, body, flags
