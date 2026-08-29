---
name: transcript-ingest
description: "Drop a meeting transcript → normalize to wiki/raw/ convention → write a wiki/sources/ summary → extract candidate decisions (flagged, NEVER auto-locked) → append a wiki/log.md row. Use when the user says they dropped a transcript in wiki/raw, or asks to ingest this transcript, file this meeting, or process this meeting transcript."
user-invocable: true
argument-hint: "<transcript-path> [--type standup|design-session|discovery-sync|general]"
disable-model-invocation: true
---

# transcript-ingest — meeting transcript → wiki pipeline

You are the **librarian**. A meeting transcript has been dropped into `wiki/raw/` (or a path
was passed directly). Your job: normalize the filename to convention, read it, produce a
summary into `wiki/sources/`, extract candidate decisions (flagged only — never
auto-locked), append a log row, and surface the candidates for human follow-up via
`promote-to-ledger`.

**Tier:** wiki (librarian) — optimistic git, no locks. Do NOT touch the decision log —
promotion goes through the change-managed tier via `promote-to-ledger`.

If this repo has a separate standup-digest skill installed, offer to hand off standup-type
transcripts to it after filing; otherwise summarize the standup inline using the Meeting
Overview structure below.

## Sensitive-data discipline (non-negotiable)

If this repo handles regulated personal data (e.g. patient records), never record names,
identifiers, dates of birth, or other identifying personal findings in any produced artifact.
Reference such data by resource type and UUID only (e.g. "Document resource
`doc-uuid-1234`", never a real name). This rule applies to: the normalized raw file path,
the `wiki/sources/` summary, the candidate-decision list, and the `wiki/log.md` row.

## Naming convention (inherits wiki-ingest)

Normalized raw filenames follow: `{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}`

- `{YYYY-MM-DD}` — meeting date (not ingest date; ask the user if it cannot be parsed
  from the file header/content).
- `{INITIALS}` — auto-derived from `git config user.name` (first letter of each word,
  uppercase). Falls back to `user.email` prefix, then prompts if neither resolves.
- `{slug}` — meeting-type + short topic in kebab-case (e.g. `design-session-workspace-model`,
  `standup`, `discovery-sync-iam-layer`).
- Flat `wiki/raw/` when total file count is below ~20; month subfolders
  `wiki/raw/{YYYY}/{MM}/` otherwise. Same rule as `wiki-ingest`.

Normalize (rename) any human drop that does not already match this convention. The original
filename is never preserved.

## Provenance (inherits wiki-ingest)

Every `wiki/sources/<slug>.md` page carries:
- `created_by`: initials of the ingestor — set at first ingest, never overwritten.
- `updated_by` + `updated`: refreshed on every re-ingest.

Derive from git identity, not user input.

## Inputs

- Transcript path (ask if not given; default to most recently added file under `wiki/raw/`
  or `_INBOX/`, whichever is newer).
- `--type` hint (optional): `standup | design-session | discovery-sync | general`.
  If omitted, infer from filename or first lines of the transcript.

## Steps

### Step 0 — Sweep `_INBOX/`

Before ingesting a named path, check whether `_INBOX/` contains any files (excluding
`.gitkeep` and `README.md`). If files are present and no explicit path was given:

```bash
find _INBOX/ -type f ! -name '.gitkeep' ! -name 'README.md'
```

Classify each file:
- **Transcript** → process here (continue with Step 1 below).
- **Note / idea / doc** (no speaker turns, no meeting structure) → route to
  `/wiki-ingest <path>` instead (see `wiki-ingest` SKILL.md — do not duplicate routing
  logic; that skill owns note/doc handling).
- **Decision-shaped** → route through wiki ingest and flag as candidate for
  `/promote-to-ledger` (never auto-locked).

Move the identified transcript from `_INBOX/` to a working path before normalization;
delete the `_INBOX/` original once the source page is successfully written.

If no files are found in `_INBOX/` and no path was given, prompt the user.

### Step 1 — Detect transcript type

Read the first 30 lines of the transcript. Classify as one of:
- `standup` — short (< 30 min), per-person Yesterday/Today/Blockers format
- `design-session` — technical design, architecture, or workflow discussion
- `discovery-sync` — initiative/product discovery, stakeholder alignment
- `general` — all other meeting types

**If `standup`:** after completing steps 2–7 below, produce the per-person digest inline
(Yesterday/Today/Blockers, traffic-light status) using the summary body, or hand off to a
dedicated standup-digest skill if this repo has one installed.

**If `design-session` or `discovery-sync`:** after completing steps 2–7, note to the user
that a deeper, code-grounded pass may be valuable if this repo has such a skill installed —
do not attempt to fabricate one. The librarian capture you filed here stands on its own.

### Step 2 — Normalize the raw filename

Reuse the wiki-ingest normalize helper:
```bash
CANONICAL="$(bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/normalize-raw.sh" \
  <path-to-transcript>)"
```

If the script is not available (path not found), perform the normalization manually:
derive date + initials + slug + extension, rename the file, and note the old and new names.

Use `${CANONICAL}` for all subsequent steps. The raw file is immutable after normalization.

### Step 3 — Read the transcript

Read `${CANONICAL}` in full. Build an internal model of:
- **Meeting date, type, and attendees**
- **Speaker turns** and key discussion threads
- **Action items and blockers** mentioned
- **Potential decisions** — statements that commit to a course of action, rule out an
  alternative, or answer an open question (collect these for Step 5)

### Step 4 — Scaffold the source page (deterministic bookkeeping)

Derive `<slug>` from the normalized filename (strip date prefix and initials):
```bash
RAW_REL="${CANONICAL#*/wiki/raw/}"
bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/new-source.sh" \
  <slug> "${RAW_REL}" "<one-line summary for the log>"
```

If `wiki/sources/<slug>.md` already exists (re-ingest), skip `new-source.sh` and instead:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/update-source-provenance.sh" \
  wiki/sources/<slug>.md
```

### Step 5 — Fill the source summary body

Edit `wiki/sources/<slug>.md`. Structure:

```markdown
## Meeting Overview

- **Date:** YYYY-MM-DD
- **Type:** standup | design-session | discovery-sync | general
- **Attendees:** [comma-separated names/initials]
- **Duration (approx):** NN min

## Summary

[3–8 sentence summary. Cite speaker where attribution helps. No regulated personal data —
resource types + UUIDs only, if this repo handles such data.]

## Key Points

- [Load-bearing claim 1]
- [Load-bearing claim 2]
- …

## Action Items

| Owner | Action | Due |
|-------|--------|-----|
| [initials] | [concrete next step] | [date or "TBD"] |

## Candidate Decisions

> **These are CANDIDATES only — not locked.** Use `/promote-to-ledger` to move
> any item into the decision log after human review.

| # | Candidate | Context | Suggested type |
|---|-----------|---------|----------------|
| 1 | [one-line decision candidate] | [why it looks like a decision] | discovery / critical_decision / layer_item |
| … | … | … | … |

## Cross-links

[wikilinks to related wiki/entities/, wiki/synthesis/, or wiki/sources/ pages]
```

**Decision candidate rules:**
- Only surface items that have a clear "we will / we won't / we chose X" shape.
- Never include items that are questions, action items, or "we should think about X."
- Mark each candidate's suggested type (discovery, critical_decision, layer_item) based
  on scope and impact — but do not assign an ID or write to the decision store.
- A candidate that merely restates an already-locked decision is noted as "already
  captured" and NOT listed as a new candidate.

### Step 6 — Update wiki/index.md (if needed)

Update `wiki/index.md` only if the transcript introduces a new top-level category.
Keep the index terse — categories + one-line summaries, not a per-file list.

### Step 7 — Append wiki/log.md row

Append a new row to `wiki/log.md` (append-only — never edit existing rows):
```
| YYYY-MM-DD | ingest | wiki/sources/<slug>.md | <one-line summary> — N candidate decisions surfaced. |
```

### Step 8 — Refresh the search index

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/wiki-query/scripts/qmd-search.sh" status
tools/wiki-index/refresh-bm25-index.sh
```

Note in the log if a vector/rerank refresh was skipped (opt-in, see `tools/wiki-index/README.md`).

## Post-ingest output to user

After completing all steps, present a concise report:

```
Transcript filed: wiki/sources/<slug>.md
Log updated: wiki/log.md row appended
Candidate decisions: N items (listed below)

Candidate decisions — review and use /promote-to-ledger for any you want to lock:
1. [candidate summary]
2. …
```

## Acceptance (self-check before finishing)

- [ ] Raw transcript is normalized to `{YYYY-MM-DD}-{INITIALS}-{slug}.{ext}`
- [ ] `wiki/sources/<slug>.md` exists with meeting overview, summary, key points, action items,
      and candidate decisions (clearly flagged as CANDIDATES — not locked)
- [ ] `wiki/log.md` has the new dated ingest row
- [ ] No regulated personal data in any produced artifact
- [ ] Candidate decisions have NOT been written to the decision log
- [ ] For standup transcripts: a digest was produced (inline or via a dedicated skill)

## Gotchas

- **This skill is user-only** (`disable-model-invocation: true`) — it writes to `wiki/raw/`
  and `wiki/sources/`; it must never self-invoke on a passing mention of a meeting.
- **Candidate decisions are flagged, never locked** — this skill must not write directly to
  the decision log; promotion is a separate, human-gated step (`/promote-to-ledger`).
- **The raw transcript is immutable after normalization** — do not edit or delete it once
  the canonical filename is set, even to fix a typo.
- **Deeper repo-specific summary passes are opt-in, not automatic** — for design-session /
  discovery-sync transcripts, only offer such a pass if this repo has one installed; never
  fabricate or auto-run a skill that doesn't exist.
- **Sensitive-data discipline applies to every produced artifact** — the normalized
  filename, the summary, the candidate list, and the log row, not just the transcript body.

## Constraints

- No regulated personal data (names, identifiers, DOB, other identifying personal findings) anywhere,
  if this repo handles such data.
- Candidate decisions are presented for human review — the skill never writes into the
  decision log directly.
- Do not modify or delete the raw transcript after normalization.
- Do not migrate other existing wiki content — file only the single dropped transcript.
