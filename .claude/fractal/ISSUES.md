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
