---
name: wiki-ingest
description: "Ingest a raw source dropped in wiki/raw/ into the wiki — normalize the filename to convention, read it, write a summary into wiki/sources/, stamp OKF provenance frontmatter, update wiki/index.md, and append a dated line to wiki/log.md. Risky edits (shrink / overwrite / dropped-provenance) are quarantined under _review-queue/ instead of landing directly. The librarian ingest loop. Use when the user says they dropped a file in wiki/raw, or asks to ingest this into the wiki, file this source, or summarize and file this into the wiki."
user-invocable: true
disable-model-invocation: true
---

# wiki-ingest — the librarian ingest loop

You are the **librarian**. A raw source has been dropped into `wiki/raw/` (a PDF, transcript,
clipping, or note). Your job is the deterministic ingest loop: normalize the filename,
read it, summarize it, stamp provenance, file the summary, cross-link it, and record the
operation. **Low friction — file everything.** New or heavily-edited pages that trip a risk
signal go through the review queue instead of landing directly — see that section below.

This is the **wiki (librarian) tier**: optimistic git, no locks. Do NOT touch a repo's
separate change-managed decision log — see `promote-to-ledger`.

## Naming convention

Raw files follow: `{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}`

- **Flat `wiki/raw/`** is the default when total file count is below ~20.
- **Month subfolders** `wiki/raw/{YYYY}/{MM}/` are used when total file count reaches 20+.
- Initials are auto-derived from `git config user.name` (first letter of each word,
  uppercase). Falls back to `user.email` prefix, then prompts if neither is set.
- A human drop that does not match the convention is **normalized (renamed)** on ingest — the
  original filename is never preserved. The raw file is otherwise immutable after normalization.

### What is ingestable (exclusion rules)

The librarian only files **document sources**. Two kinds of input are never swept into the wiki:

1. **`_`-prefixed paths** — any file under or named `_*` (e.g. `_drafts/`, `_INBOX/`,
   `_review-queue/`, `_anything.md`). The leading underscore is the "working material,
   not a source — preserve but do not index" marker. These are kept as raw provenance inside a
   preserved bundle (see Bundle handling) but **never get a `wiki/sources/` summary page**.
2. **Non-document files** — only `.md` and `.pdf` are ingestable. Scripts (`.sh`), data
   (`.tsv`, `.csv`), `.txt` fragments, `.gitignore`, etc. are skipped. They may ride along inside
   a preserved raw bundle but are never summarized or normalized into the source pool.

These exclusions are enforced in the Step-0 sweep `find` itself — not left to judgment — so a
naive "ingest `_INBOX/`" cannot vacuum scripts, ticket fragments, or superseded drafts.

> **Two layers — the sweep is only half.** Skipping `_`-paths in the sweep stops them getting a
> `wiki/sources/` *summary* page, but the search index scans the whole `wiki/` tree on
> `**/*.md` by default, so a preserved `_`-dir's markdown (e.g. `_drafts/` docs) is still
> *searchable raw* unless the index config is told to ignore it — see the `ignore` globs
> already applied in `tools/wiki-index/refresh-bm25-index.sh`. After preserving any new
> `_`-dir under `wiki/`, re-run the refresh script and confirm a term unique to the `_`-dir
> returns nothing.

## Provenance (OKF v0.2)

Every `wiki/sources/<slug>.md` page carries:
- `okf_version: "0.2"`, `type: source`.
- `created_by`: initials of the ingestor, set at first ingest (never overwritten).
- `updated_by` + `updated`: refreshed on every re-ingest.
- `source:` — the wiki-relative path(s) the page was distilled from.

These fields are derived from git identity, not user input.

## Inputs

- The path of the dropped file (ask the user if not given; default to the most recently added
  file in `wiki/raw/` or `_INBOX/`, whichever is newer).

## Steps

### Step 0 — Sweep `_INBOX/`

Before ingesting a named path, check whether `_INBOX/` contains ingestable input. The sweep
applies the exclusion rules above (`.md`/`.pdf` only; no `_`-prefixed paths) directly in `find`:

```bash
# Ingestable sources only: .md/.pdf, never README, never any _-prefixed path component.
find _INBOX/ -type f \( -name '*.md' -o -name '*.pdf' \) ! -name 'README.md' ! -path '*/_*'
```

Then split the results into **loose files** (directly in `_INBOX/`) and **bundles** (files that
live inside a non-`_` subdirectory of `_INBOX/`, e.g. `_INBOX/timeline-drafts/…`):

- A subdirectory containing **2+ ingestable `.md` files** is a **bundle** → route the whole
  directory to **Bundle handling** below (do NOT process its files one-by-one through the loose
  path; that would flatten the bundle and break its cross-links).
- Everything else is a **loose file** → classify and process individually:
  - **Transcript** (filename contains `standup`, `meeting`, `sync`, `session`, or the file
    starts with speaker-turn markers like timestamps or `NAME:`) → route to
    `/transcript-ingest <path>` (see `transcript-ingest` SKILL.md — do not duplicate routing
    logic here; that skill owns transcript handling).
  - **Decision-shaped** (file contains clear "we will / we won't / we chose" statements) →
    proceed with wiki ingest AND flag the item as a candidate for `/promote-to-ledger` in
    the source summary's Candidate Decisions section. Never auto-lock.
  - **Note / idea / doc** (everything else) → proceed with wiki ingest below.

For a **loose file**, move it from `_INBOX/` to a working path in `wiki/raw/` before
normalization, then delete the `_INBOX/` original once the source page is successfully written.
If no ingestable input is found in `_INBOX/` and no path was given, prompt the user.

### Step 0.5 — Bundle handling (multi-doc folders)

A **bundle** is a coherent multi-document folder (a deliverable pack, a meeting-prep set, a
timeline pack) — not a loose drop. The single-source loop (Steps 1–7) would flatten it into
disconnected pages and dissolve its reading order; bundles get the **hybrid** treatment instead:
preserve the raw folder intact, write one summary page per top-level doc, and add one bundle
index page that ties them together.

1. **Preserve the raw bundle intact.** Move the whole directory to `wiki/raw/bundles/<bundle>/`,
   structure unchanged. The `_`-prefixed subdirs and any non-`.md` files **ride along
   preserved but are not summarized** — they are raw provenance, reachable from the index but
   absent from the source pool.
   ```bash
   BUNDLE="offline-vault-timeline-drafts"   # the _INBOX subdir name
   mkdir -p wiki/raw/bundles
   git mv "_INBOX/${BUNDLE}" "wiki/raw/bundles/${BUNDLE}" 2>/dev/null \
     || mv "_INBOX/${BUNDLE}" "wiki/raw/bundles/${BUNDLE}"
   ```
   Raw bundle files are immutable after the move — do not rename them (their intra-bundle relative
   links must keep resolving). The per-file rename convention does NOT apply inside a bundle.

2. **One source page per top-level `.md`** (excluding `_`-paths). For each, run `new-source.sh`
   with a bundle-namespaced slug and the preserved raw path, then fill the summary (Step 4 rules):
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/new-source.sh" \
     "${BUNDLE}--<doc-slug>" "bundles/${BUNDLE}/<file>.md" "<one-line summary>"
   ```
   Cross-link each page back to the bundle index with `[[<bundle>--index]]` and to its siblings.

3. **One bundle index page.** Create `wiki/sources/<bundle>--index.md` summarizing the bundle as a
   whole: what it is, the reading order, a one-line entry per member doc linking its source page,
   and a pointer to the preserved raw bundle (incl. a note on what `_`-dirs hold). This page is the
   navigable entry point that replaces the lost folder structure.

4. **Decision-shaped members** still get flagged as `/promote-to-ledger` candidates in their own
   source page's Candidate Decisions section. Never auto-lock.

5. Then continue to Steps 5–7 (index/log/re-index) **once for the whole bundle** — one `wiki/log.md`
   `ingest` row per source page is fine, but refresh the index a single time at the end.

> **Granularity rule of thumb:** give a member its own source page when it is independently useful
> in search; if a folder is really one document split across files, prefer a single index page that
> summarizes the whole and skip per-file pages. Default to per-file pages for numbered/titled
> deliverables (they answer different questions), index-only for fragmentary working sets.

### Step 1 — Normalize the raw filename

Run the helper to enforce the naming convention:
```bash
CANONICAL="$(bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/normalize-raw.sh" \
  <path-to-dropped-file>)"
```
Use `${CANONICAL}` as the authoritative path for all subsequent steps. If the file was
renamed, note the old and new names.

2. **Read the raw source.** Read `${CANONICAL}`. If it is binary (PDF), use the appropriate
   tool. After normalization the raw file is immutable — do not edit it.

3. **Scaffold the source page** (deterministic bookkeeping):
   ```bash
   # Derive relative path from repo-root/wiki/raw/
   RAW_REL="${CANONICAL#*/wiki/raw/}"
   bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/new-source.sh" \
     <slug> "${RAW_REL}" "<one-line summary for the log>"
   ```
   - `<slug>` — kebab-case, descriptive (e.g. `nova-notification-transport-gist`).
   - Creates `wiki/sources/<slug>.md` from an OKF v0.2 template (with `created_by` stamped)
     and appends an `ingest` row to `wiki/log.md`.
   - If `wiki/sources/<slug>.md` already exists (re-ingest), skip `new-source.sh` and instead
     run the provenance updater — but route the new body through the **review queue** first
     (Step 3.5 below), since a re-ingest is exactly the "LLM-written edit to an existing page"
     case the queue exists for.

### Step 3.5 — Review queue (risky edits)

Any edit to an **existing** `wiki/sources/`, `wiki/synthesis/`, or `wiki/entities/` page —
a re-ingest, a re-synthesis, a manual revision — goes through the risk-based quarantine gate
before it lands, never a direct overwrite:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/review-queue.sh" apply \
  <existing-page-path> <path-to-your-new-content> --actor "$(git config user.initials 2>/dev/null || echo unknown)" \
  --reason "<why this page is being re-ingested/revised>"
```

The script checks three mechanical risk signals — it does not judge content quality:

1. **Shrink** — the new body is less than 50% the byte size of the current body.
2. **Dropped provenance** — the current page has a non-empty `source:` or `created_by:`
   frontmatter key that the new content lacks.
3. **Explicit `--overwrite`** — pass this yourself when you know the edit is a full replace
   (not a merge) and want the check to apply regardless of size.

- **Exit 0** — no risk signal tripped; the edit was applied in place. Continue to Step 4.
- **Exit 2** — quarantined under `_review-queue/<queue-id>--<basename>`, target left
  untouched. Tell the user: *"This edit shrinks/overwrites/drops provenance on
  `<page>` — quarantined for review at `_review-queue/<queue-id>--...`. Run
  `review-queue.sh approve <queue-id>` to apply it, or `reject <queue-id> --reason ...` to
  discard it."* Do NOT work around the quarantine by editing the target directly.

A brand-new page (via `new-source.sh`, no prior file to compare against) never quarantines —
the risk model only applies to edits of existing content.

### Step 4 — Fill the summary body

Edit `wiki/sources/<slug>.md` (or, if the page went through the review queue, edit the
*queued* content, then re-run `review-queue.sh apply` so the improved version is reassessed):
   - A faithful 3–8 sentence summary (cite section/page where useful).
   - Key points as bullets — the load-bearing claims only.
   - Cross-links: `[[wikilinks]]` to related `wiki/entities/` and `wiki/synthesis/` pages. Create a
     stub entity page in `wiki/entities/` if the source introduces a new person/concept/topic.
   - For a `wiki/synthesis/` page, include the three-way link-provenance split — `## See also`,
     `## Backlinks`, `## Related (semantic)` — per `docs/wiki-conventions.md`.

### Step 5 — Update `wiki/index.md`

Only if a new top-level category appeared. The index is a catalog of categories + one-line
page summaries, not a per-file list — keep it terse.

### Step 6 — Refresh the search index

```bash
tools/wiki-index/refresh-bm25-index.sh
```
Run `bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh" status` first to
confirm the index location. The refresh is BM25-only and fast (no model load); a
vector/rerank refresh is a separate, opt-in step — see `tools/wiki-index/README.md` — note
in the log if skipped.

### Step 7 — Confirm the log line

`wiki/log.md` must have a new `| <date> | ingest | wiki/sources/<slug>.md | … |`
row. The log is append-only — never edit existing rows.

## Acceptance (self-check before finishing)

**Loose file:**
- [ ] Raw file is normalized to `{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}`; in a `{YYYY}/{MM}/`
      subfolder if total raw file count is 20+.
- [ ] `wiki/sources/<slug>.md` exists with a real summary, `okf_version: "0.2"`, and
      `created_by` frontmatter.
- [ ] `wiki/log.md` has the new dated `ingest` row.
- [ ] Cross-links added; new entity stubs created if warranted.
- [ ] Normalized raw source is untouched after normalization.
- [ ] A re-ingest of an existing page went through `review-queue.sh apply`, not a direct edit.
- [ ] `tools/wiki-index/qmd-search.sh search "<a phrase from the summary>"` returns the new page.

**Bundle:**
- [ ] Raw folder preserved intact at `wiki/raw/bundles/<bundle>/`; `_`-dirs and non-`.md` files
      rode along but were NOT renamed or summarized.
- [ ] One `wiki/sources/<bundle>--<slug>.md` per top-level `.md`; one `<bundle>--index.md`.
- [ ] No `wiki/sources/` page was created for anything under a `_`-prefixed path.
- [ ] Index page lists reading order + links every member page + points at the preserved raw bundle.
- [ ] Index refreshed once; a member phrase is retrievable.

## Gotchas

- **This skill is user-only** (`disable-model-invocation: true`) — it writes to
  `wiki/sources/`, `wiki/index.md`, and `wiki/log.md`; it must never self-invoke.
- **`_`-prefixed paths and non-`.md`/`.pdf` files are never swept** — the Step-0 `find`
  enforces this in the command itself, not in judgment; don't hand-ingest a `_drafts/` file.
- **A bundle (2+ ingestable `.md` in one subdir) must not be flattened** — route it to
  Bundle handling, or cross-links between its members break.
- **A re-ingest is an edit of existing content, not a fresh page** — it always goes through
  `review-queue.sh apply`, even when you're confident the change is safe. The gate is
  mechanical, not a trust judgment.
- **`review-queue.sh`'s risk model is purely mechanical** (byte-size ratio, frontmatter key
  presence) — it has no opinion on whether the *content* is good. A quarantined edit may be
  entirely correct; that's what the approve step is for.
- **The search index needs an explicit `ignore` glob for `_`-dirs** — otherwise a preserved
  `_`-dir's markdown stays searchable even though it has no source page.

## Constraints

- A+ clean markdown only. No raw HTML, no exec blocks.
- Sensitive-data discipline: if this repo handles regulated personal data, never record it —
  resource type + UUID only, if applicable.
- Do not migrate other existing content in a single ingest call — this skill files the
  single dropped source (or bundle) it was invoked on.
