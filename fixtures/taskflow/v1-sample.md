# NOVA Discovery Log — v1 format sample

> **Synthetic fixture.** This file renders one fixture decision (`D-0003`) in the **v1 discovery-log table format** so the v1 → v2 importer has a worked example to parse. The canonical v2 form of the same decision is `decision-log/D-0003.md`; if the two ever disagree, the v2 entry wins.
>
> Format A columns: `| ID | Question | Why It Matters | Owner | Status | Answer |` under a `## Layer N — Name` heading. Status uses the v1 emoji markers (🟢 answered, 🟡 in discovery, 🔴 open, 🔶 conflicted, 🔵 pending sign-off, ⚫ deferred).

---

## Activity Log

| Date | What changed | Reference(s) | Downstream effect |
|------|--------------|--------------|-------------------|
| 2026-08-17 | mergeloom ratified as the vault sync library; family (replicated types) already settled 2026-08-12. | D-0003 | Unblocks WS-4, WS-5, WS-6. Adds 34 kB client dependency. |
| 2026-08-14 | Library evaluation landed — three candidates against five criteria. | D-0003 | Recommendation drafted for ratification. |
| 2026-08-12 | Design session chose the replicated-data-type family over operational transform. | D-0003, D-0001 | Library choice deferred to evaluation. |

---

## Layer 4 — Technical

| ID | Question | Why It Matters | Owner | Status | Answer |
|----|----------|---------------|-------|--------|--------|
| D-0003 | Which convergent-replicated-type library backs the offline vault sync, and what happens to the merges it cannot settle? | The vault is the whole Phase 2 promise. A library that discards a losing value irrecoverably destroys user work rather than merely annoying, and the clock format decides whether the sync protocol can piggyback on the existing channel or has to invent a second ordering scheme. | AR | 🟢 Answered | **RV-R 2026-08-14:** Evaluated three candidates against five criteria (bundle size, tombstone GC, exposed clock, maintainer responsiveness, enumerable divergence). mergeloom 34 kB, incremental GC, documented clock, first-class unresolved-set API. driftset 21 kB but manual compaction only, internal clock, and last-writer-wins discards the losing value irrecoverably. weaveline 88 kB with a 340 ms stop-the-world compaction pause. **[AR-A 2026-08-17]: Ratified — mergeloom adopted.** Carries the residue rule: the merge settles structure, not intent; every same-field text rewrite surfaces to a review queue with both candidate values intact. See D-0001 (the channel this rides on). |
