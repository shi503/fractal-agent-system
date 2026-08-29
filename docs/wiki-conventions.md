# Wiki Conventions

The `fractal-wiki` plugin (`.claude/plugins/fractal-wiki/`) operates on a markdown knowledge
substrate rooted at `wiki/` (in this repo, the fixture corpus lives at
`fixtures/taskflow/wiki/` — see `fixtures/taskflow/README.md`). This document describes the
substrate's shape, its frontmatter contract, the three-way link-provenance split, and the
risk-based review queue that gates LLM-written edits.

## 1. Substrate shape — four tiers

```
wiki/
├── index.md          # catalog: tiers, categories, one-line summaries — not a per-file list
├── log.md             # append-only operation log (ingest/synthesis/decision/lint rows)
├── raw/                # captured sources, normalized filenames, immutable after normalization
│   └── {YYYY}/{MM}/{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}
├── sources/            # distillations — one page per raw source (or bundle member)
├── synthesis/          # cross-cutting reads over multiple source pages
└── entities/           # stubs for people, systems, and recurring concepts
```

- **`raw/`** is the immutable capture layer. `wiki-add` / `wiki-ingest` / `transcript-ingest`
  write here; nothing downstream edits a raw file after normalization.
- **`sources/`** is a faithful distillation of one raw file (or one bundle member) — summary,
  key points, cross-links. Every `sources/` page's frontmatter carries `source:` pointing
  back at the raw file(s) it was built from.
- **`synthesis/`** is a cross-cutting read across multiple `sources/` pages — the place an
  argument spanning several distillations gets made once instead of repeated. Every
  `synthesis/` page carries `source:` listing every page it draws from, and closes with the
  three-way link split (§3).
- **`entities/`** are lightweight stubs for a person, system, or recurring concept that
  multiple other pages need to reference — created on demand when a source or synthesis page
  introduces something worth a stable anchor.

`raw/` file count below ~20 stays flat; at 20+ it moves to `{YYYY}/{MM}/` month subfolders
(enforced by `wiki-ingest`'s `normalize-raw.sh`, not left to judgment).

## 2. Frontmatter contract — OKF v0.2

Every file in the substrate carries:

```yaml
---
okf_version: "0.2"
type: index | log | raw | source | synthesis | entity | note | meeting
title: "..."
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
created_by: "AR"      # initials, derived from git identity, never hand-typed
updated_by: "AR"
status: ACTIVE | SUPERSEDED | ARCHIVED
---
```

`source:` (a list of wiki-relative paths) is additionally required on `sources/` and
`synthesis/` tier pages — it is the field the three-way link split's provenance half and
`wiki-ingest`'s review-queue dropped-provenance check both key off.

`wiki/index.md` and `wiki/log.md` must exist at exactly those lowercase paths — tooling
(`wiki-lint`'s OKF conformance mode, `tools/wiki-index/`) assumes it. See
`fixtures/taskflow/wiki/index.md` and `fixtures/taskflow/wiki/log.md` for worked examples.

`wiki-lint` runs OKF conformance as a deterministic first pass (required `type:`,
`okf_version`, the lowercase index/log paths) before its qualitative checks — see that
skill's `SKILL.md`.

## 3. The three-way link-provenance split

A `synthesis/` (or any heavily cross-referenced) page distinguishes **why** a link exists —
three sections, never merged into one undifferentiated link list:

```markdown
## See also

Documents this page was built from or that continue its argument directly.

- `wiki/sources/foo.md` — the comparison behind §1

## Backlinks

Documents that reference this page.

- `decision-log/D-0001.md` — cross-references this synthesis

## Related (semantic)

Neighbours by subject rather than by citation — surfaced by retrieval, not asserted
by an author.

- `wiki/entities/some-system.md` — the system this architecture instantiates
```

- **See also** — authorial, forward-looking: what this page explicitly draws from or
  continues. Matches the page's `source:` frontmatter for a `synthesis/` page.
- **Backlinks** — authorial, backward-looking: what elsewhere in the repo cites *this* page.
  Maintained by hand or by a lint pass that walks the link graph — never inferred from
  search.
- **Related (semantic)** — retrieval-surfaced, not asserted: neighbours a search found by
  subject, not because any author linked them. Keeping this section separate from the first
  two is the point — it tells a reader "the machine thinks this is relevant" is a different
  claim from "the author cited this."

Worked example: `fixtures/taskflow/wiki/synthesis/nova-architecture-synthesis.md` carries all
three sections against the four source pages it draws from, the decision/workstream/blueprint
docs that cite it back, and two semantically-related entity/raw pages.

`wiki-lint` flags a `synthesis/` page missing any of the three sections as a Medium finding.

## 4. The review queue — risk-based quarantine for LLM-written edits

An LLM editing an *existing* wiki page can silently do damage in three specific ways:
shrink it, overwrite it wholesale instead of merging, or drop its provenance frontmatter.
`wiki-ingest` routes every edit to an existing `sources/`, `synthesis/`, or `entities/` page
through `.claude/plugins/fractal-wiki/skills/wiki-ingest/scripts/review-queue.sh` (referenced
as `${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/review-queue.sh` from inside a skill)
before it lands — a brand-new page is never subject to this gate, only an edit of something
that already exists.

**Risk signals (any one trips quarantine):**

| Signal | Trigger |
|--------|---------|
| Shrink | proposed body is less than 50% the byte size of the current body |
| Dropped provenance | current page has a non-empty `source:` or `created_by:` that the new content lacks |
| Explicit `--overwrite` | caller declares the edit is a full replace, not a merge |

**Flow:**

```bash
review-queue.sh apply <target> <new-content> --actor <INITIALS> --reason "<why>"
```

- **Not risky** → applied in place immediately, exit 0.
- **Risky** → the proposed content is copied to `_review-queue/<queue-id>--<basename>`, the
  target is left untouched, exit 2. A row is appended to `_review-queue/QUEUE.md`
  (append-only, `PENDING` status).

A human (or a deliberate follow-up session) resolves a pending entry:

```bash
review-queue.sh approve <queue-id> --actor <INITIALS>   # applies the queued content to its target
review-queue.sh reject  <queue-id> --actor <INITIALS> --reason "<why>"  # discards it, target untouched
review-queue.sh list                                      # show all PENDING entries
```

Both actions append a new manifest row (`APPROVED` / `REJECTED`) rather than editing the
`PENDING` row in place — the manifest is a full audit trail, not just a current-state table.

`_review-queue/` itself is `_`-prefixed, so `wiki-ingest`'s sweep and the search index both
skip it automatically (see `wiki-ingest`'s exclusion rules and the `ignore` globs in
`tools/wiki-index/refresh-bm25-index.sh`) — a quarantined draft never becomes searchable or
gets swept as a source until it is explicitly approved.

`wiki-lint` flags any `_review-queue/` entry still `PENDING` after a few days as a High
finding — an unreviewed quarantine is maintenance debt, not a safe steady state.
