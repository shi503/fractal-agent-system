# Decision Ledger v2 — v1-Table Import Pattern

This directory carries the **pattern** for importing a legacy discovery log
kept as markdown tables into Decision Ledger v2 entries, plus **one worked
example** against the fixture corpus. It is not a general-purpose importer:
a real project's v1 source almost always has its own table dialects and
owner-naming conventions, and porting every one of those company-specific
parsing rules is explicitly out of scope here. What's worth carrying across
is the shape of the pipeline and the parts of it that are genuinely generic.

## Why "pattern, not parser"

A v1 → v2 importer has three layers, and only the first two travel well:

1. **Parse** — turn a markdown table row into a structured record (generic:
   any project's discovery log is some dialect of `| ID | ... |` rows).
2. **Transform** — map that record's fields onto the v2 schema: status via
   an emoji table, RACI via `XX-R`/`XX-A`/`XX-C`/`XX-I` suffix extraction,
   cross-refs via ID-pattern regexes, a title via sentence extraction. All
   of this is genuinely project-agnostic *if* it's parameterised by a
   caller-supplied set of known initials, rather than a hardcoded roster.
3. **Resolve** — turn a raw "Owner" column value (which in a real org's
   discovery log is often something like `"Eng + Product"` or a full name)
   into initials. This step is where every real deployment differs, because
   it encodes a specific team's org chart and column conventions. It does
   not belong in a portable pattern.

`v1_pattern.py` implements layers 1 and 2. Layer 3 is left to a thin,
project-specific adapter script — `convert_v1_sample.py` is that adapter for
the TaskFlow fixture, and it is intentionally small (it resolves an owner
column that already contains bare initials, which is the easy case).

## Module map

| File | Purpose |
|------|---------|
| `v1_pattern.py` | Generic helpers: status mapping, cross-ref extraction, "Format A" table parsing, RACI-suffix extraction, title/date extraction, body assembly |
| `convert_v1_sample.py` | The one worked example: converts `fixtures/taskflow/v1-sample.md` into a valid v2 entry |
| `test_import_pattern.py` | Unit tests for the generic helpers + an end-to-end test of the worked example |

## The worked example

```bash
python3 tools/decision-ledger/import-pattern/convert_v1_sample.py
```

This reads `fixtures/taskflow/v1-sample.md` (a single-row v1-format table
under `## Layer 4 — Technical`, describing the same decision as
`fixtures/taskflow/decision-log/D-0003.md`), parses the row, transforms it
into v2 frontmatter + body, validates the result against `schema.yaml` and
`fixtures/taskflow/people.yaml`, and prints the rendered entry.

Pass `--out <path>` to write the converted entry to disk instead of a temp
file, or `--source` / `--people` to point at a different v1 source or
people registry.

## v1 → v2 field mapping (Format A table)

| v2 field | Source |
|----------|--------|
| `id` | ID column |
| `type` | Supplied by the caller (the table section determines this — a discovery-log table is all one type) |
| `title` | First sentence of the Question column |
| `status` | Emoji or text in the Status column (🟢 → answered, 🔴 → open, etc.) |
| `owner` | Owner column, if it already contains bare initials resolvable against the people registry; otherwise flagged for manual review |
| `raci` | `XX-R` / `XX-A` / `XX-C` / `XX-I` suffixes found in the Answer + Status text, restricted to known initials; falls back to the resolved owner as `responsible` |
| `layer` | Supplied by the caller (the section heading determines this) |
| `created` / `updated` | Earliest/latest `YYYY-MM-DD` date found in the Answer + Status text; falls back to caller-supplied defaults |
| `created_by` / `updated_by` | First `responsible` RACI actor |
| `cross_refs` | D-/CD-/BI-/L#- IDs found in the Question + Answer text |
| `addenda` | `[IMPORT] FLAG:` messages for anything that couldn't be mapped cleanly |
| Body `## Context` | "Why It Matters" column |
| Body `## Answer` | Answer column, preserved verbatim |
| Body `## Unmapped Fields` | Present only when there are flags; never a silent drop |

## Content-fidelity rule

Never silently drop answer text, cross-refs, or body content. If a field
can't be mapped cleanly, it goes into `flags`, which land in both the
frontmatter's `addenda` and the body's `## Unmapped Fields` section — a
human reviews it, nothing just vanishes.

## Extending this to a full-corpus importer

A project that wants to import its own v1 discovery log should:

1. Write a project-specific owner → initials resolver (layer 3 above) —
   this is almost always the only genuinely new code required.
2. If the source uses more than one table dialect (a "Format B" with
   inline emoji-embedded answers, a Critical-Decisions register with a
   different column set, etc.), add a parser function alongside
   `parse_format_a_table()` following the same shape: take the section
   text and an ID regex, return a list of `V1Record`.
3. Drive `transform_record()` over the parsed records and write each
   result through `storage.store.DecisionStore.write()` (or the CLI's
   `dl write`), one entry at a time, so the safety layer's lock checks and
   the schema validator both run on every write.
4. Keep re-running conversions idempotent — a v1 source often gets
   re-imported as it's edited during the migration, and overwriting a v2
   entry with a freshly re-converted version should be safe and expected.
