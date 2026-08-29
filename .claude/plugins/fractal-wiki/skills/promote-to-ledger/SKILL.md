---
name: promote-to-ledger
description: "Promote a wiki note (usually a candidate decision from a transcript-ingest or synthesis page) into a schema-valid decision-log entry via the DecisionStore CLI. Runs RACI/ownership questions, writes through the storage layer, never raw-files into the decision log. Includes an explicit refusal path when a lock is held. Use when the user asks to promote to ledger, lock this decision, promote this wiki note, move this to the decision log, promote a candidate, or file this decision."
user-invocable: true
argument-hint: "<wiki-source-path or candidate #N from transcript-ingest output> [--entry-id D-NNNN]"
disable-model-invocation: true
---

# promote-to-ledger — wiki note → decision ledger

You are the **librarian-to-ledger bridge**. A candidate decision has been surfaced in the
wiki tier (via `transcript-ingest`, `wiki-ingest`, or `wiki-query`). Your job: guide the user
through the deliberate promotion path — clarify ownership and RACI, then write a
schema-valid decision entry via the `dl` (Decision Ledger) CLI.

Wiki notes are NOT silently promoted; this skill is the gate.

**Tier:** decision-log — change-managed, locked writes. All writes go through
`tools/decision-ledger/storage/cli.py`. Never write `.md` files into the decision log
directly.

## Inputs

One of:
- A path to a `wiki/sources/<slug>.md` file containing a `## Candidate Decisions` section.
- A candidate number from a prior `transcript-ingest` output (e.g., `candidate #3`).
- A `--entry-id` to update an existing entry (for adding a wiki note to a pre-existing
  `open` entry).

If invoked bare, ask the user to paste or point to the candidate they want to promote.

## Configuration

```
DL_ROOT     = fixtures/taskflow/decision-log   # default; override for a real (non-fixture) decision log
DL_CLI      = tools/decision-ledger/storage/cli.py
VALIDATE_PY = tools/decision-ledger/schema/validate.py
PEOPLE_YAML = tools/decision-ledger/schema/people.yaml
```

`DL_ROOT` is configurable per repo — this default points at the fixture corpus. A repo
running this skill against its own decision log should override `DL_ROOT` (e.g. in a
project-level config note, or by asking the user) rather than hand-editing this file.

## Steps

### Step 0 — Load context

Read these files before doing anything else:

1. `tools/decision-ledger/schema/schema.yaml` — entry types, statuses, required fields.
2. `${PEOPLE_YAML}` — known initials for RACI validation (do not hardcode a name list here;
   always resolve initials against this file so the skill stays correct as people change).

Run:
```bash
python3 tools/decision-ledger/storage/cli.py --store "${DL_ROOT}" list
```

Build an internal model of:
- Next available D-ID number (scan `${DL_ROOT}/*.md` filenames; increment highest)
- Existing CD/BI IDs to avoid collision
- Any entries with status `open` or `in_discovery` that this candidate might be
  describing (surfacing a match avoids creating a duplicate)

### Step 1 — Read the source

If the user provided a `wiki/sources/<slug>.md` path, read that file and extract
the `## Candidate Decisions` table. Present the candidates in a numbered list via
`AskUserQuestion`:

```
Which candidate do you want to promote?

1. [candidate title] — [context snippet]
2. …
N. [candidate title] — [context snippet]

Or paste your own decision text if it's not listed above.
```

If the user provides raw text (not from a list), accept it as the decision statement.

### Step 2 — Duplicate check

Search the current decision-log for any entry whose title closely matches the candidate
title. If a strong match is found, present it:

```
This looks similar to an existing entry:

  [ID] — [title] — status: [status]

Do you want to:
  (a) Update that existing entry instead of creating a new one
  (b) Create a new entry (if this is genuinely distinct)
  (c) Cancel — this is already captured
```

Use `AskUserQuestion`. If (c), stop here. If (a), proceed with updating the existing
entry at Step 5 (skip the type/layer questions — those are already set).

### Step 3 — Classify the entry

Ask via `AskUserQuestion` (two prompts). Read the exact type list and ID patterns from
`tools/decision-ledger/schema/schema.yaml` (`entry_types`) rather than assuming this list
is exhaustive — a repo may have added or renamed a type there.

**Prompt 1 — Entry type:**
```
What type of decision is this?

- discovery — an open question that needs an answer (D-NNNN)
- critical_decision — binary, high-impact, gates progress (CD-NNN)
- layer_item — scoped to a specific layer of the initiative (L#-NN)
- big_idea — a strategic lever that unlocks multiple items (BI-NNN)
```

**Prompt 2 — Layer (if discovery, critical_decision, or layer_item):**
```
Which layer does this belong to? (cross-layer if it spans multiple)
```
List the layer identifiers this repo actually uses (see `schema.yaml` / any layer registry
this repo maintains) rather than a fixed list. Skip Prompt 2 for `big_idea` entries.

### Step 4 — RACI and ownership interview

Ask via `AskUserQuestion` (two prompts):

**Prompt 1 — Responsible:**
```
Who is Responsible for answering / making this decision?
```
List the known initials from `${PEOPLE_YAML}` here (do not hardcode names — read the file
fresh each run). Validate each initial against that file. If unknown: warn the user (will
be recorded as an external contributor, RACI = C). Do not block — the user may be adding a
new team member.

**Prompt 2 — Accountable (optional):**
```
Who is Accountable (ratifies the final decision)?
Press Enter to default to the Responsible person.
```

Inform the user: Consulted and Informed fields can be added later via a follow-up edit to
the same entry.

### Step 5 — Title and body

Ask via `AskUserQuestion`:
```
Confirm the one-line title for this decision entry.
(Suggested: [candidate title from wiki source])
```

Accept edits. Then construct the body:

```markdown
## Context

[Paste the full candidate context from the wiki source. Include a backlink to the
source wiki page: "Source: wiki/sources/<slug>.md"]

## Answer

_Not yet answered._

## Cross-refs

- Source: wiki/sources/<slug>.md
- [any related IDs mentioned in the candidate context]
```

### Step 6 — Lock check + write via the storage layer

Assign the next available ID based on the entry type selected in Step 3, per the ID
patterns in `schema.yaml` (e.g. `discovery` → next `D-NNNN`, `critical_decision` → next
`CD-NNN`, `big_idea` → next `BI-NNN`, `layer_item` → `L{N}-NN`).

#### Step 6a — Acquire lock

```bash
python3 tools/decision-ledger/storage/cli.py \
  --store "${DL_ROOT}" \
  lock <ENTRY-ID> --actor <INITIALS>
```

**If lock is held by another actor — explicit refusal path:**

Parse the error output to extract the lock holder's initials and expiry time. Surface
to the user immediately — do NOT proceed:

```
PROMOTION REFUSED — the decision store is currently locked by [OTHER-INITIALS].

Entry:   [ENTRY-ID] — [title]
Locked:  [OTHER-INITIALS] (expires ~[time])

Options:
  (a) Wait — retry in 60 seconds (I will try again automatically)
  (b) View-only — show the current entry without editing
  (c) Force-unlock — take the lock from [OTHER-INITIALS]
      (requires an audit reason; use only if [OTHER-INITIALS] is unreachable)
  (d) Cancel — abandon this promotion
```

Use `AskUserQuestion` to present all four options. If (c) chosen, require a free-text
audit reason, then:
```bash
python3 tools/decision-ledger/storage/cli.py \
  --store "${DL_ROOT}" \
  unlock <ENTRY-ID> --actor <OTHER-INITIALS>
```
Re-acquire the lock. Log the force-unlock in the commit message:
`[FORCE-UNLOCK by <INITIALS>: <audit-reason>]`.

If (d) chosen: stop. Inform the user no write was made.

#### Step 6b — Build and write entry

Construct the `dl write` call:
```bash
python3 tools/decision-ledger/storage/cli.py \
  --store "${DL_ROOT}" \
  write <ENTRY-ID> \
  --actor <INITIALS> \
  --set "id=<ENTRY-ID>" \
  --set "type=<entry-type>" \
  --set "title=<title>" \
  --set "owner=<responsible-initials>" \
  --set "status=open" \
  --set "layer=<L#>" \
  --set "created=<ISO-TIMESTAMP>" \
  --set "updated=<ISO-TIMESTAMP>" \
  --set "created_by=<INITIALS>" \
  --set "updated_by=<INITIALS>" \
  --body "<body-text>"
```

The `dl write` command is atomic (temp-file + rename). Do not write the file directly.

#### Step 6c — Validate

```bash
python3 tools/decision-ledger/schema/validate.py "${DL_ROOT}/<ENTRY-ID>.md"
```

If validation fails, show the error and ask the user to correct the input. Do NOT commit
a validation-failing entry. Common issues:
- Missing required fields (especially `raci`)
- `id` pattern mismatch (check `schema.yaml`'s `id_pattern`)
- ISO-8601 timestamp format errors

#### Step 6d — Sensitive-data lint

If this repo's decision log could plausibly receive regulated personal data (e.g. patient
records), run a lint pass before commit:
```bash
grep -E '(national_id|date_of_birth|full_name|street_address|[0-9]{3}-[0-9]{2}-[0-9]{4})' \
  "${DL_ROOT}/<ENTRY-ID>.md"
```

If any match is found, block the commit and ask the user to rephrase (reference resource
types/UUIDs, not identifying data). Re-run write + lint until clean. Skip this step
entirely for a repo/fixture with no regulated-data surface.

#### Step 6e — Release lock

```bash
python3 tools/decision-ledger/storage/cli.py \
  --store "${DL_ROOT}" \
  unlock <ENTRY-ID> --actor <INITIALS>
```

### Step 7 — Commit

```bash
git add "${DL_ROOT}"
git commit -m "chore(ledger): <ENTRY-ID> promoted from wiki — <title> — <INITIALS>-R"
```

Confirm to the user:
```
Promoted: <ENTRY-ID> — <title>
Status: open (awaiting answer)
Source: wiki/sources/<slug>.md

The decision is now tracked in the decision log. Answer it, set RACI, and track sign-off
in a follow-up entry edit.
```

### Step 8 — Update wiki source (optional backlink)

Offer via `AskUserQuestion`:
```
Add a "promoted" note to the wiki source page?
This adds a line like "> Promoted to [ENTRY-ID] on YYYY-MM-DD" next to the candidate.
```

If yes, append the note to the relevant row in `wiki/sources/<slug>.md`'s candidate
table and commit:
```bash
git add wiki/sources/<slug>.md
git commit -m "docs(wiki): backlink <ENTRY-ID> promotion in <slug>"
```

## Acceptance (self-check before finishing)

- [ ] Entry written via `dl write` (not raw file edit)
- [ ] Schema validation passed
- [ ] Sensitive-data lint passed (or explicitly skipped for a non-regulated repo)
- [ ] Lock acquired before write, released after
- [ ] Commit contains only files under `${DL_ROOT}`
- [ ] User told the entry ID and how to continue
- [ ] No regulated personal data in entry body

## Gotchas

- **This skill is user-only** (`disable-model-invocation: true`) — it writes to the locked
  decision log; it must never self-invoke on a passing wiki mention of a decision.
- **A held lock blocks the write outright** — do not retry silently or fall back to a raw
  file edit; surface the 4-option refusal menu (wait / view-only / force-unlock / cancel).
- **`DL_ROOT` defaults to the fixture corpus** (`fixtures/taskflow/decision-log`) — a real
  deployment must override it, or every promotion lands in fixture data.
- **A sensitive-data lint runs on every entry body** before commit where applicable — a
  rephrase loop, not a bypass; never weaken the regex to get an entry through.
- **All writes go through `dl write`** — a raw `.md` edit into the decision log is never
  valid, even to "fix" a validation error faster.
- **This skill never answers the decision** — it only creates an `open` entry; answering
  and RACI sign-off happen in a follow-up edit.

## Explicit refusal paths

| Condition | Skill response |
|-----------|---------------|
| Lock held by another actor | Surface 4-option menu; do NOT write until lock is free or force-unlocked with audit reason |
| Sensitive data found in entry body | Block commit; prompt rephrase loop |
| Schema validation fails | Block commit; show errors; prompt correction |
| User says "cancel" at any step | Stop with no write and explicit confirmation: "No entry was created." |
| Candidate already promoted (duplicate detected) | Offer to update existing entry or cancel |

## Constraints

- All writes go through `python3 tools/decision-ledger/storage/cli.py` — never raw file edits.
- Never `git push` unless the user explicitly requests it.
- Never write into the decision log by any means other than the `dl write` command.
- Sensitive-data lint must pass before any commit, where applicable.
- Schema validation must pass before any commit.
- This skill does not answer the decision — it creates an `open` entry for follow-up.
