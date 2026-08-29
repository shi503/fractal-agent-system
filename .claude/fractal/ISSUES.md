# FRACTAL Issues Log

Persistent tracker for framework-level bugs and anomalies discovered during execution.
Agents append here when they encounter unexpected router, skill, or agent behavior.
The Architect triages OPEN issues before authoring each new BLUEPRINT phase.

**Severity levels:** CRITICAL (breaks state machine / blocks execution) | WARN (degrades quality) | MINOR (polish)
**Lifecycle:** OPEN → resolved by a workstream HANDOFF that fixes it → update Status to RESOLVED + link HANDOFF

---

## Template — Add New Issues Below

```markdown
## [YYYY-MM-DD] [SEVERITY] Short title

**Discovered by:** [Agent or workstream name]
**Symptom:** [What happened — concrete steps or invocation]
**Impact:** [Why it matters — state corruption, wrong output, blocked workflow]
**Recommended fix:** [What change would resolve it — file, behavior, or doc update]
**Status:** OPEN | RESOLVED — [brief note or HANDOFF link]
---
```

---

## [2026-03-17] [MINOR] package.json#prisma.seed deprecated in Prisma 6

**Discovered by:** FeatureLead-SchemaPrisma (M1.1 handoff eval)
**Symptom:** `npx prisma validate` emits: "The configuration property `package.json#prisma` is deprecated and will be removed in Prisma 7."
**Impact:** Non-blocking — seed still runs. Will break in Prisma 7.
**Recommended fix:** Move seed config into `prisma.config.ts`, remove `"prisma"` key from `package.json`.
**Status:** OPEN

---

## [2026-08-28] [WARN] No `sync-from-blueprint` mode — adding workstreams to a BLUEPRINT requires a destructive `init`

**Discovered by:** router.py 2.0.0 promotion audit
**Symptom:** When a BLUEPRINT file gains new workstreams after `.state.json` already exists, there is no way to register just the new entries. `router.py init` is the only command that (re-)builds `.state.json` from the blueprint, and it overwrites the file wholesale — any `IN_PROGRESS`/`COMPLETE` status already recorded for existing workstreams is wiped and reset to `NOT_STARTED`.
**Impact:** Mid-epic BLUEPRINT expansion (a new phase or workstream added to an active epic) forces a choice between losing tracked progress (`init`) or hand-editing `.state.json`'s flat `{workstream: status}` map to add the missing keys — workable since the format is additive-safe, but manual and easy to get wrong under time pressure.
**Recommended fix:** Add a `router.py sync-from-blueprint` command that diffs the blueprint's workstream set against `.state.json`, adds any missing keys as `NOT_STARTED`, and leaves every existing key untouched.
**Status:** OPEN

---

## [2026-08-28] [MINOR] No `BLOCKED` or `IN_REVIEW` states

**Discovered by:** router.py 2.0.0 promotion audit
**Symptom:** `cmd_update` only accepts `NOT_STARTED | IN_PROGRESS | COMPLETE`. A workstream that is waiting on an external decision, or that is implemented and awaiting review before being marked `COMPLETE`, has no state that represents that — it is either left `IN_PROGRESS` (indistinguishable from active work) or force-marked `COMPLETE` early.
**Impact:** `router.py status` and `router.py next` cannot distinguish "actively being worked" from "stalled/blocked" or "done pending review," so the state-machine view understates how much of an epic is actually stuck.
**Recommended fix:** Extend the valid-statuses list with `BLOCKED` and `IN_REVIEW`, and teach `cmd_next` to treat both as non-`NOT_STARTED` (i.e. not re-offered) without counting as `COMPLETE` for dependency resolution.
**Status:** OPEN
