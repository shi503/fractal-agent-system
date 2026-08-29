---
name: grounded-meeting-summary
description: "Digest a feature/architecture or discovery meeting transcript into a grounded, gold-standard summary. Disambiguates via the shared glossary, then grounds every design assumption against the deployed code/stack (a code/stack synthesis doc when provided, else a search over the target repo) so readers act on deployed reality instead of re-deriving primitives. Emits a workflow/topic digest + decisions register + ADR candidates + issue-tracker mapping + architecture diagram. Runs repo-local; writes the canonical summary back to the planning repo's project meetings home. Use when the user asks to ground this meeting, produce a grounded meeting summary, or summarize a design session or architecture meeting."
user-invocable: true
argument-hint: "<transcript.md path> [--synthesis <code/stack synthesis .md>] [--repo <target-repo-path>] [--project <name>] [--type design-session|discovery-sync]"
---

# grounded-meeting-summary — the grounded planning artifact

You produce the **grounded** distillation of a feature/architecture or discovery meeting — the
27/27 tier of the meeting-summary rubric, not the librarian-tier capture. The output is a stored,
durable planning artifact (decisions register, ADR candidates, tracker mapping), **not** a chat paste.

**The distinguishing lens is _grounding_ (rubric D3).** Design discussions routinely propose
behaviour that the deployed stack **already provides or already constrains**. Your job is to check
each meeting assumption against deployed reality and surface — with **citations** — where the room
re-derived an existing primitive, contradicted the deployed model, or introduced a migration risk.
A code-blind summary is the librarian tier; a wiki-ingest pass already does that. This skill is the
architect tier.

> **Why this runs repo-local.** Grounding requires the code. An agent that cannot read the target
> repo's source produces a materially weaker D3 — it can only restate the room back to itself.

---

## Step 0 — Inputs and execution context

Parse arguments (ask in one batched `AskUserQuestion` if invoked bare):

| Arg | Meaning | Default |
|-----|---------|---------|
| transcript path | path to the raw transcript `.md` | required |
| `--synthesis <doc>` | a same-period **code/stack synthesis** to ground against | none → ground by searching the repo |
| `--repo <path>` | the **target repo** whose code/stack the design concerns | the cwd repo |
| `--project <name>` | project whose meetings home receives the canonical output | inferred from the repo |
| `--type` | `design-session` \| `discovery-sync` | infer from the transcript |

**Execution-context rules (a GATE — resolve these before Step 1):**
- **Grounding runs repo-local** — working directory = `--repo`. Load that repo's `CLAUDE.md` and its
  code. If a human is already in a session in the target repo, they invoke this skill there.
- **If the planning repo is the driver** and `--repo` is a sibling checkout, **dispatch a sub-agent
  pinned to that repo's working directory** to do the grounding read. That sub-agent grounds; the
  **canonical summary is written back to the planning repo** under
  `projects/<project>/meetings/active/{date}/`. The skill is entry-point agnostic — never hardcode
  one path.
- **The grounding actor is the Architect, always.** Grounding spans code *and* the project plan; it
  is not routed by meeting type.
- **Output is canonical in the planning repo** regardless of where the pass ran (bidirectional write).

---

## Step 1 — Read the transcript in full

Read the entire raw file. Build a model of: attendees (plus the **referenced-not-present** roster),
purpose, the **workflows/topics** walked, decisions, deferred items, open/parked questions, action
items, and every **design assumption** ("we'll put invitation state in X", "login must take a tenant
param", "billing grants the role"). Those assumptions are what you ground in Step 3.

---

## Step 2 — Disambiguation pre-edit (produce ONE normalized cleaned-transcript)

**Apply the shared glossary FIRST:** `wiki/entities/glossary.md` (repo-relative) — confirmed
`heard → canonical` mappings grouped by proper nouns, tools, acronyms, and roster. Apply them
silently. Only ask the user about terms **not** covered there, or where transcript context
contradicts a glossary row.

**Roster check (mandatory):** any name not in the attendee list → confirm it is a real teammate
(check the glossary's people/roster section first), and record it under **Non-attendee mentions**.

**Normalize the filename and merge into ONE cleaned transcript — do not leave two files.** Raw
meeting exports arrive with tool-generated names (`Some Long Title - 2026_08_12 16_00 - Transcript.md`).
Two fixes, both mandatory:

1. **Rename to convention:** `{YYYY-MM-DD}-{topic-kebab}-transcript.md`. Compute `source_hash`
   (`sha256sum`) of the **original raw bytes BEFORE renaming or merging** — that hash is the
   reprocess-on-edit anchor and must reflect the pristine export.
2. **Merge, don't split:** produce a **single** file = a disambiguation/correction header
   (frontmatter `layer: cleaned-transcript`, `source_original_filename`, `source_hash`, a glossary
   reference; then the mapping table, the roster check, and any load-bearing corrections)
   **followed by the verbatim transcript body under a `## Raw transcript (verbatim — unedited)`
   heading**. The body stays byte-for-byte unedited — corrections live in the header tables, never
   inline — so the one file is both the citable record and the human-readable source. Do **not**
   emit a separate `*-cleaned.md` alongside the raw; that orphans two files and breaks links. The
   simplest mechanic: write the header, then `cat header raw > {normalized-name}` and remove the
   original raw.

(The output home follows the GATE and `--project` rules, plus any explicit user path — same as the
summary in Step 5.)

New mistranscriptions you resolve with the user → append them to `wiki/entities/glossary.md` under a
dated `## LLM Update — YYYY-MM-DD` section (append-only; never overwrite human-authored rows). That
is how the glossary compounds.

---

## Step 3 — GROUNDING (the differentiator — rubric D3)

For **each** design assumption from Step 1, check it against deployed reality:

1. **If `--synthesis <doc>` was provided:** read it. It is the authoritative current-state audit.
   Ground each assumption against its sections. Cite as `synthesis §N`, plus the file or function
   when the synthesis names one.
2. **Else:** ground by searching the target repo — the repo's committed lexical/BM25 index if it has
   one, otherwise `grep`/`rg` — together with the repo's plan, decision log, and `CLAUDE.md`. Cite
   the `file:line` the claim came from. On a resource-constrained box prefer the lexical index over
   any embedding-based path; a slow retrieval path is not a reason to skip grounding.
3. **Read the actual code** when the synthesis or the search points at a function or endpoint and
   the claim is load-bearing (a token TTL, a session model, a bootstrap path). Grounding that cites
   code beats grounding that cites prose.

For each grounded assumption, emit an inline **🔎 Grounding** callout that does one of:
- **Confirms** that the room re-derived an existing, documented gap or plan ("this is already
  tracked and epic'd; the audit already names the stores") — useful confirmation, flagged as
  not-greenfield.
- **Contradicts / corrects** ("login is identity-based; the tenant is a post-auth token-mint concern —
  login need not take a tenant param"). This is the highest-value output the skill produces.
- **Flags an already-handled primitive** ("the identity service already represents inactive
  identities natively").
- **⚠️ Flags a migration risk or tension** ("this reverses the façade removal from two releases ago;
  re-introducing it is its own ticket").

**Hard rule: every 🔎 callout cites a source.** A callout with no `synthesis §`, `file:line`, or
function reference is not grounding — it is opinion. Delete it or find the citation.

---

## Step 4 — Emit the gold-standard structure

Reproduce the 9-dimension structure (see `references/format-note.md` for the annotated skeleton and
`references/rubric.md` for the bar). Sections, in order:

1. **Format note** — one line: adapted from `meetings-standup-summary` for a feature/architecture
   session; the distinguishing lens is grounding; name the companion synthesis doc.
2. **Header table** — Date/duration · Attendees (initials) · **Non-attendee mentions** · Purpose ·
   tracker epic · design branch · companion synthesis doc · external artifacts.
3. **TL;DR** — 2–4 bullets, each leading with a **traffic-light** (🟡/🔴/🟢) plus a session-level 🔎
   grounding flag.
4. **Disambiguation pass** — the applied mapping table and roster check (D2).
5. **Architecture in one picture** — an **ASCII diagram** orienting the reader (e.g. the
   apps → services → infrastructure model), plus a core-thesis line, plus a 🔎 grounding callout on
   the headline (D6).
6. **Workflow-by-workflow (or topic-by-topic) digest** — per item: **proposed shape →
   decisions/changes → 🔎 grounding** wherever the stack already speaks to it (D1/D3).
7. **Cross-cutting themes** — atomicity, role taxonomy, and so on; each with its own 🔎 grounding
   (D3/D7).
8. **Decisions register** — a 3-column table **✅ Decided (attribution) | 🟡 Deferred (revisit) |
   ❓ Open/Parked**, every row attributed to a speaker (D4).
9. **ADR candidates** — each parked debate becomes an ADR with a **grounded proposed disposition**
   and a ticket reference (D5).
10. **Tracker / story mapping** — meeting theme → real ticket table (D5).
11. **Action inventory** — per-owner concrete next steps (D5).
12. **Sources** — transcript link, companion synthesis (the grounding source), external docs,
    precedent-format link, AI-processed signoff (`agent · skill (adapted) · @Name`).

**Risk/migration flags (D7):** wherever a decision tensions with the current posture, surface it
explicitly (⚠️) in the relevant section AND in the decisions register.

---

## Step 5 — Write canonical output + index

- **Path:** `projects/<project>/meetings/active/{YYYYMMDD}/MEETING-SUMMARY-{date}-{topic}.md` **in
  the planning repo** (canonical, per the GATE). If you ran repo-local in a sibling checkout, write
  back here.
- **Frontmatter (reprocess-on-edit):**
  ```yaml
  ---
  date: YYYY-MM-DD
  type: design-session | discovery-sync
  source: <relative path to the normalized cleaned-transcript from Step 2>
  source_hash: <sha256 of the ORIGINAL raw bytes, pre-merge/pre-rename>   # maintenance flags stale on mismatch
  synthesis: <path to the grounding synthesis, if any>
  grounded_by: Architect
  status: ACTIVE
  ---
  ```
  Compute the hash from the pristine export **before** Step 2 renames or merges it:
  `sha256sum <raw-transcript>`.
- **Cross-link:** add a row to the project meetings index/README; link the cleaned transcript from
  Step 2 and the companion synthesis.
- **Index:** confirm the output path falls under an indexed collection and re-scan. Note in the
  output if the semantic index was skipped and only the lexical index was refreshed.
- **Do NOT** commit; do NOT run `router.py`. The Architect owns commits and router state.

---

## Step 6 — Self-score on the rubric (always)

Score the output you just produced against the 9 dimensions in `references/rubric.md` (0–3 each).
Report the table and the total. **Bar for a grounded summary: ≥24/27, with D3 (grounding) ≥2 and a
non-empty set of cited 🔎 callouts.** If D3 < 2, or any 🔎 callout lacks a citation, you have produced
a librarian-tier capture rather than a grounded summary — go back to Step 3.

When run as the **acceptance test** (re-grounding a transcript that already has a manual gold
standard), additionally **diff** your output against that gold standard and report the delta per
dimension.

---

## Routing (how this skill is reached)

A transcript-ingest pass classifies the drop. For `design-session | discovery-sync` it **offers**
the grounded pass — never auto-runs it, because grounding is the expensive path. For `standup` it
delegates to `meetings-standup-summary`. This skill is the architecture-session sibling of
`meetings-standup-summary` and reuses its disambiguation engine.

## Gotchas

- **An un-cited 🔎 callout is the one unrecoverable defect.** It reads exactly like grounding and is
  exactly opinion. Cite or delete.
- **Hash before you rename.** The `source_hash` must be of the pristine export. Computing it after
  the Step 2 merge silently breaks every future staleness check.
- **Two files is a bug.** A separate `*-cleaned.md` beside the raw orphans links; merge into one.
- **The synthesis doc is authoritative over the room.** When the transcript and the synthesis
  disagree, the summary says so — that disagreement is the artifact's whole value.

## What you are NOT doing

- Not producing a chat paste — this is a stored artifact (that is `meetings-standup-summary`).
- Not locking decisions — the decisions register and ADR candidates are **candidates**; locking runs
  through the promote-to-ledger flow after human review.
- Not editing the transcript **body** — it stays verbatim. Corrections live in the disambiguation
  header merged into the single normalized cleaned transcript (Step 2); do not leave a separate
  `*-cleaned.md` orphan or a tool-generated raw filename.
- Not emitting an un-cited 🔎 callout — grounding without a source is opinion.
- Not committing, and not running `router.py`.
