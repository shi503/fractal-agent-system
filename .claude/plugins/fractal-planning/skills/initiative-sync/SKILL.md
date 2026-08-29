---
name: initiative-sync
description: "Sync an initiative's planning state from a source repo into this planning repo. Classifies changed files into three pipelines — raw inputs (1:1 copy), state docs (merge + conflict surface), drafts (quarantine + reground) — and maintains a provenance manifest under the initiative's migrated/ directory. Idempotent and repeatable. Use when the user asks to sync initiative state from another repo, pull planning docs across from a sibling checkout, migrate a discovery log between repos, or reconcile two copies of the same initiative."
user-invocable: true
argument-hint: "(optional) \"dry-run\" to preview without writing, or a source repo name/path override"
disable-model-invocation: false
---

# Initiative Sync

You perform a structured sync of an initiative's planning state from a **source repo** into **this
planning repo**. Two repos that share an initiative usually do not share an architecture — naive
copying creates silent architectural drift, where a draft written against one stack lands as if it
were true of another. This skill categorizes each changed file and applies the right pipeline.

**Two paths you resolve at Step 1 and use throughout:**

| Variable | Meaning |
|----------|---------|
| `INITIATIVE_ROOT` | the initiative's directory, relative to a repo root, identical on both sides (e.g. `projects/<project>/`) |
| `SOURCE_ROOT` | absolute path to the source repo root |

`TARGET_ROOT` is this repo. Everything below is expressed relative to those three — never hardcode a
machine path.

---

## First Principles

1. **Content type dictates sync strategy.** Meeting notes, state docs, and drafts move differently.
2. **Provenance is non-negotiable.** Every migrated file records source repo, source commit (when
   available), source mtime, and migration date.
3. **Architecture boundaries are sticky.** Drafts reference a tech stack. Regrounding is explicit,
   reviewable, and never silent.
4. **The discovery log is append-consensus.** Conflicts between repos are surfaced, not
   auto-resolved.
5. **Idempotent.** Re-running with no new source changes is a no-op. Hash-compared, not
   timestamp-compared.

---

## Step 1 — Source Selection

Ask via `AskUserQuestion`:

- Question: "Which source repo are we syncing from?"
- Options: the sibling checkouts this repo knows about, plus **Other path** — the user enters an
  absolute path via the Other input.

If "Other", ask a follow-up free-text question: "Enter the absolute path to the source repo root
(the repo containing the initiative directory)."

Then confirm `INITIATIVE_ROOT` — offer the path this repo uses and let the user override it if the
source repo files the same initiative under a different directory.

**Validate** the source path:
- The path must exist.
- `${SOURCE_ROOT}/${INITIATIVE_ROOT}` must exist.
- If either check fails, print the error and stop — do not fall back to a guess.

Record `SOURCE_REPO` (basename) and `SOURCE_ROOT` (absolute path) for use throughout.

Also ask via `AskUserQuestion`:
- Question: "Dry-run or commit?"
- Options:
  - **Dry-run (recommended for a first pass)** — classify and diff, write nothing, produce a report
  - **Execute** — run the pipelines, write files, update the manifest, stage for commit

Store `MODE = dry-run | execute`.

---

## Step 2 — Snapshot Both Sides

Run via Bash (in parallel where the calls are independent):

```bash
# Source commit context (if the source is a git repo)
git -C "${SOURCE_ROOT}" log --oneline -n 1 -- "${INITIATIVE_ROOT}" 2>/dev/null || echo "not-a-git-repo"
git -C "${SOURCE_ROOT}" rev-parse HEAD 2>/dev/null

# Target commit context
git log --oneline -n 1 -- "${INITIATIVE_ROOT}"
```

Record `SOURCE_COMMIT` (short hash) for provenance. If the source is not a git repo, set it to
`unknown` and carry on — that is a supported case, not an error.

Enumerate both file trees:

```bash
find "${SOURCE_ROOT}/${INITIATIVE_ROOT}" -type f \
  -not -path '*/node_modules/*' -not -path '*/.git/*' | sort > "${TMPDIR:-/tmp}/isync_source.txt"

find "${INITIATIVE_ROOT}" -type f \
  -not -path '*/node_modules/*' -not -path '*/.git/*' | sort > "${TMPDIR:-/tmp}/isync_target.txt"
```

---

## Step 3 — Classify Each File

For each file in the source tree, compute a path relative to `INITIATIVE_ROOT` and assign a
**category** by path match (first rule wins):

| Category | Path pattern | Pipeline |
|----------|-------------|----------|
| **RAW_INPUT** | `src/**`, `meetings/**`, `meeting-notes/**`, `briefs/**` | A — 1:1 copy |
| **STATE_DOC** | the initiative framework and discovery-log state docs (e.g. `00-*-Framework.md`, `01-Discovery-Log.md`) | B — merge + conflict surface |
| **DRAFT** | `drafts/**` | C — quarantine + reground |
| **ROOT_DOC** | `README.md` and any other top-level `.md` not matched above | B (treat as a state doc) |
| **SKIP** | anything else (`.DS_Store`, editor backups, build output) | log + skip |

For each file, compute **status**:
- **NEW** — exists in source, not in target
- **IDENTICAL** — hashes match (`shasum -a 256`)
- **MODIFIED** — exists in both, hashes differ
- **DELETED_IN_SOURCE** — exists in target at the same relative path but not in source — report
  only, never delete

Build a classification table for the report.

---

## Step 4 — Run Pipelines

Skip every write if `MODE == dry-run` — build the plan and show it in the report (Step 6).

### Pipeline A — RAW_INPUT (1:1 copy)

For each NEW or MODIFIED raw input:
1. `mkdir -p` the target directory.
2. Copy the file (`cp -p` preserves mtime).
3. Record a manifest entry.

Rationale: meeting notes, raw source docs, and briefs are append-only facts. We want them
byte-identical on both sides.

### Pipeline B — STATE_DOC (merge + conflict surface)

State docs are large and their merges are additive — new discovery items, new activity-log rows, new
layer updates. An overwrite silently discards whichever side was not chosen.

For each MODIFIED state doc:
1. **Write a target-side snapshot** to `${INITIATIVE_ROOT}/migrated/_conflicts/{filename}.local.{YYYY-MM-DD}.md`
   — preserving what this repo has right now.
2. **Copy the source to a staging path**: `${INITIATIVE_ROOT}/migrated/_conflicts/{filename}.incoming.{YYYY-MM-DD}.md`.
3. **Generate a conflict report** at `${INITIATIVE_ROOT}/migrated/_conflicts/{filename}.diff.{YYYY-MM-DD}.md`
   using `diff -u`, truncated to the first 400 lines plus a total line count.
4. **Do NOT overwrite the live target.** This is a human merge. Print the conflict file paths in the
   final report and tell the user:
   > The live framework and discovery-log docs were NOT overwritten. Review the diff files under
   > `migrated/_conflicts/` and merge manually — the Architect resolves discovery-item conflicts; see
   > the `initiative-interview` skill for that flow.

For NEW state docs (unusual at the root level but possible): copy in place and flag for Architect
review.

### Pipeline C — DRAFT (quarantine + reground)

Drafts encode architecture decisions that belong to the source repo's stack and may not hold in
this one. They cannot be copied in place.

For each NEW or MODIFIED draft:
1. Copy source → `${INITIATIVE_ROOT}/migrated/drafts/{relative_subpath}/{filename}` (quarantine).
2. Create or append a row in `${INITIATIVE_ROOT}/migrated/_deltas/{relative_subpath}__{filename}.md`
   carrying:
   - Source path + commit
   - Migration date
   - Status: `QUARANTINED — awaiting regrounding`
   - **Architecture drift scan**: grep the quarantined file for the stack terms that differ between
     the two repos and list every hit. Build that term list at Step 1 from the two repos' own
     `CLAUDE.md` / README stack sections — framework names, ORM or data-layer names, auth provider,
     runtime, and the source repo's own name used as a path reference. Terms are per-repo-pair; do
     not hardcode a list here.
3. **Do NOT write to the canonical `drafts/` tree.** The Architect (or a follow-on workstream) reads
   the quarantined file plus the drift scan, then produces the regrounded version at
   `${INITIATIVE_ROOT}/drafts/{subpath}/{filename}` with a banner:
   ```
   > **[REGROUNDED: YYYY-MM-DD from {SOURCE_REPO}@{shortsha}]**
   > Architecture drift resolved: {what changed} (see migrated/_deltas/{...}.md).
   ```

### Pipeline D — SKIP

Log the relative path and the reason to the report.

---

## Step 5 — Update Manifest

Append to (or create) `${INITIATIVE_ROOT}/migrated/MANIFEST.md`:

```markdown
# Migration Manifest — {initiative}

Cross-repo provenance for files migrated into this repo from sibling copies of the same initiative.
See the `initiative-sync` skill for the pipeline definitions.

## Run Log

### {YYYY-MM-DD HH:MM} — from {SOURCE_REPO}@{SOURCE_COMMIT}

**Mode:** {dry-run | execute}
**Operator:** {initials}
**Totals:** {N new, M modified, K identical, X conflicts, Y quarantined, Z skipped}

| Rel path | Category | Status | Pipeline | Destination |
|----------|----------|--------|----------|-------------|
| meetings/2026-08-12/... | RAW_INPUT | NEW | A | same path |
| 01-Discovery-Log.md | STATE_DOC | MODIFIED | B | migrated/_conflicts/01-Discovery-Log.diff.2026-08-22.md |
| drafts/technical/L4-12-... | DRAFT | MODIFIED | C | migrated/drafts/technical/L4-12-... |

**Conflicts requiring human merge:** {list file paths}
**Drafts awaiting regrounding:** {list file paths}
```

If `MODE == dry-run`, still write the manifest entry with `mode: dry-run` — the manifest *is* the
plan output.

---

## Step 6 — Final Report

Print a concise summary to the user (≤200 words):

```
Sync from {SOURCE_REPO}@{SOURCE_COMMIT} ({MODE})
────────────────────────────────────────────────
  📄 Raw inputs:     {N new, M modified, K identical}
  📋 State docs:     {N modified → conflict files written}
  📐 Drafts:         {N quarantined, architecture drift in {X}}
  ⏭️  Skipped:        {N files}

Next actions:
  1. {If state-doc conflicts} Review migrated/_conflicts/*.diff.{date}.md and merge into the live docs.
  2. {If drafts quarantined} Reground each via Architect review (read migrated/_deltas/*, then emit
     the regrounded version into the canonical drafts/ tree).
  3. Commit when done: chore(discovery): sync from {SOURCE_REPO}@{SOURCE_COMMIT} — {N files}

Manifest: {INITIATIVE_ROOT}/migrated/MANIFEST.md
```

---

## Step 7 — Commit Gate

**Do NOT auto-commit.** State docs need a human merge and drafts need regrounding — either can leave
the tree half-synced.

Ask via `AskUserQuestion` only if `MODE == execute`:

- Question: "Stage and commit the raw-input and manifest changes now?"
- Options:
  - **Stage + commit raw inputs and manifest only** — a safe partial commit; state-doc merges and
    draft regrounding land in follow-up commits
  - **Leave unstaged** — the user reviews and commits manually

If commit is chosen, stage only the raw-input and manifest paths:

```bash
git add "${INITIATIVE_ROOT}/migrated/" "${INITIATIVE_ROOT}/src/" \
        "${INITIATIVE_ROOT}/meetings/" "${INITIATIVE_ROOT}/briefs/"
git commit -m "chore(discovery): sync raw inputs from ${SOURCE_REPO}@${SOURCE_COMMIT}"
```

Never stage the framework doc, the discovery log, or the canonical `drafts/` tree in this skill —
those are human-merge territory.

**Never push.**

---

## Arguments

- `dry-run` — force `MODE = dry-run` (overrides the Step 1 prompt)
- an absolute path — force it as `SOURCE_ROOT` (overrides the Step 1 prompt)
- no args — ask interactively

---

## Gotchas

- **Hash-compare, never timestamp-compare.** A `cp` without `-p`, or a fresh clone, resets every
  mtime and makes an idempotent re-run look like a full resync.
- **The drift-term list is per-repo-pair.** A hardcoded list rots the moment either repo changes
  stack; derive it at Step 1 from the two repos' own stack docs.
- **A dry-run still writes the manifest.** That is deliberate — the manifest is the plan, and a sync
  with no manifest entry did not happen.
- **`DELETED_IN_SOURCE` is a report, never an action.** The source repo deleting a file is not
  authority to delete this repo's copy.

## Constraints

- **Never delete** anything in this repo. `DELETED_IN_SOURCE` is a report, not an action.
- **Never overwrite** the framework doc, the discovery log, or the canonical `drafts/**`.
- **Never assume** the source is a git repo — handle the non-git case gracefully
  (`SOURCE_COMMIT = unknown`).
- **Never skip** the manifest write.
