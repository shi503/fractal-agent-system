# PRD — {WorkstreamName}

**Blueprint:** `.claude/fractal/{BLUEPRINT-name}.yaml`
**Workstream ID:** `{short identifier or milestone.step, e.g. M1.2}`
**Model tier:** `{sonnet | opus | haiku}`
**Owner:** Feature Lead ({initials or role})
**Depends on:** `{workstream list or []}`
**Status:** `NOT_STARTED` — update to `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, or `COMPLETE` as work progresses.

---

> **Authoring note (delete before handoff):** A Feature Lead starts fresh with no context beyond this PRD. If the PRD is ambiguous, the work will be ambiguous. Reference guides by path (e.g. `docs/guides/frontend-conventions.md`); do not paste guide content inline. Link to decisions by whatever ID scheme this repo already tracks (a linked issue, an ADR filename, a short slug) rather than re-explaining them.

## 1. Feature Overview

One paragraph: what is being built, for whom, and why this workstream exists now. Link source specs and locked decisions by ID or path.

**Source documents:**
- `path/to/spec-or-adr.md`

**Locked decisions:**
- `{decision reference}`: one-line summary

## 2. Acceptance Criteria

Specific, verifiable outcomes. Each must be independently checkable without the author present.

- [ ] …
- [ ] …
- [ ] …

## 3. Read / Write File Manifest

**Read only** (context — do not modify):
- `path/to/file`

**Write / modify** (scoped change surface):
- `path/to/file`

**Create** (new files):
- `path/to/file`

## 4. CI Gate

The workstream is not COMPLETE until this passes with zero errors on the machine executing the work.

```bash
<project build/lint/test commands — define per repo>
```

**TaskFlow example** (real scripts from `package.json`):

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

Omit sections that do not apply (e.g. a docs-only workstream skips the build/test commands entirely) and document the reduced gate here.

## 5. Session Protocol

- Heartbeat cadence: append a JSON block to `PULSE.md` every ~30 min or at task boundaries.
- On completion: generate `HANDOFF.md` (see `.claude/fractal/templates/handoff-template.md`).
- On block: set `PULSE.md` `status: BLOCKED` + `escalation_needed: true` and stop; do not guess around architectural ambiguity.

## 6. Out of Scope

Explicit non-goals. Prevents scope creep and surfaces the seam for the next workstream.

- …
- …

## 7. Blockers

**Blockers:** None

Update this section as work progresses. When resolved, convert to a "Resolved Blockers" note; do not delete the history.
