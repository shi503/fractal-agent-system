---
name: wiki-lint
description: "Periodic health check of the wiki substrate — OKF v0.2 conformance (required type:/okf_version frontmatter, lowercase index.md and log.md), contradictions, orphaned pages, stale claims, and missing cross-links across wiki/, then report findings (no silent edits). The librarian lint loop. Use when the user asks to lint the wiki, check the wiki health, check OKF conformance, or find contradictions in the wiki."
user-invocable: true
---

# wiki-lint — the librarian lint loop

You run a periodic **health check** over the wiki and produce a findings report. This is what
keeps the maintenance burden near zero. **You report; you do not silently rewrite.** Edits are
proposed, then applied only on confirmation (and large reworks go on a branch per the repo's
check-in convention).

Scope: the `wiki/` tier only. A repo's separate change-managed decision log (if any) has its
own integrity checks; do not lint it here.

## Mode: OKF v0.2 conformance (run first, deterministic)

The Open Knowledge Fixture (OKF) v0.2 contract is the substrate's frontmatter shape. Check
every `wiki/**/*.md` file:

1. **`okf_version:` present** and equal to `"0.2"` (or the version this repo has adopted —
   flag any file whose `okf_version` disagrees with the majority).
2. **`type:` present** and one of the tiers this repo uses (e.g. `index`, `log`, `source`,
   `synthesis`, `entity`, `note`, `meeting`). A missing or unrecognized `type:` is a High
   finding — every other lint pass depends on it.
3. **`wiki/index.md` and `wiki/log.md` exist, at those exact lowercase paths.** A
   capitalized or renamed variant (`Index.md`, `INDEX.md`, `Log.md`) fails conformance —
   tooling (this skill, `tools/wiki-index/`) assumes the lowercase path.
4. **Provenance keys present** (`created`, `updated`, `created_by`, `updated_by`) on every
   tier; `source:` present and non-empty on `sources/` and `synthesis/` tier pages.

Report conformance as a pass/fail count before the qualitative sections below. A repo can
require this mode to be green in CI; the qualitative sections below are always report-only.

## What else to check

1. **Orphaned pages** — pages in `wiki/sources/`, `wiki/synthesis/`, `wiki/entities/` that
   nothing links to and that are absent from `wiki/index.md`. List them; suggest a home or
   archival.

2. **Broken / missing cross-links** — `[[wikilinks]]` or relative links whose targets don't
   exist; pages that *should* cross-reference each other but don't (e.g. a source and its
   synthesis). Check the three-way link-provenance split where present (`## See also`,
   `## Backlinks`, `## Related (semantic)` — see `docs/wiki-conventions.md`): a synthesis
   page missing all three sections is a Medium finding.

3. **Contradictions** — pages making incompatible claims about the same entity/decision. Use
   the BM25 index to surface clusters, then read and compare:
   ```bash
   WRAP="${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh"
   bash "$WRAP" search "<topic that may have conflicting claims>"
   ```

4. **Stale claims** — pages with `updated:` frontmatter older than ~90 days that assert
   time-sensitive facts, or claims superseded by a later decision. Flag; suggest
   re-validation or a `status: SUPERSEDED` pointer.

5. **Log/index drift** — pages on disk with no `wiki/log.md` provenance row, or
   `wiki/index.md` categories that no longer have pages.

6. **Frontmatter hygiene** — missing `title` / `tier` / `status`, or `status` not in
   `{ACTIVE, SUPERSEDED, ARCHIVED}`.

7. **Quarantined edits** — any file under `_review-queue/` older than a few days with no
   approve/reject action is a High finding (see `wiki-ingest`'s review-queue section).

## Method

- Enumerate `wiki/**/*.md`. Build the link graph (who links whom).
- Run the OKF conformance checks deterministically (frontmatter parse, not fuzzy matching).
- Use the BM25 search to find topical clusters for the contradiction and stale-claim passes.
- For each finding record: **file:line**, category, severity (high / medium / low), and a
  one-line suggested fix.

## Output — the report

Return a structured report (do not write it into the wiki unless asked):

```
# Wiki Lint Report — <date>
Scanned: <N> pages across wiki/{sources,synthesis,entities,raw}

## OKF v0.2 conformance
<pass/fail count>; failures listed with file:line and the missing/wrong field

## High
- <finding> — <file:line> — <suggested fix>
## Medium
- ...
## Low
- ...

## Summary
<counts by category; top 3 recommended actions>
```

If asked to fix: apply only low-risk fixes (add a missing cross-link, fix a broken relative
path, add a missing `okf_version`/`type` key when the correct value is unambiguous) directly;
propose contradictions/stale-claim resolutions for human review; append a
`| <date> | lint | wiki/ | <one-line> |` row to `wiki/log.md`.

## Constraints

- No silent rewrites of content claims. Contradictions and stale facts are *reported*,
  resolved by a human (LLM-assisted) per the repo's check-in convention.
- Sensitive-data discipline applies to anything you quote in the report — resource
  type + UUID only, never raw personal data, if this repo handles regulated data.
- A+ clean markdown for any page you do touch.
