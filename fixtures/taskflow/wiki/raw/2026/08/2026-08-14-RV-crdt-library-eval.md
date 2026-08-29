---
okf_version: "0.2"
type: note
title: "CRDT library evaluation — three candidates against five criteria"
tier: raw
initiative: NOVA
created: "2026-08-14"
updated: "2026-08-14"
created_by: RV
updated_by: RV
status: ACTIVE
tags: [nova, crdt, libraries, evaluation, mergeloom]
---

# CRDT library evaluation — three candidates against five criteria

Follow-up to the 2026-08-12 design session. Three fictional candidate libraries evaluated against the five criteria AR and SP set: bundle size, tombstone garbage collection, exposed clock, maintainer responsiveness, and whether divergence is enumerable.

## Candidates

| Library | Bundle (min+gz) | Tombstone GC | Clock exposed | Maintainer | Divergence enumerable |
|---|---|---|---|---|---|
| **mergeloom** | 34 kB | yes, incremental | yes, documented | responsive, weekly releases | yes, first-class API |
| **driftset** | 21 kB | manual compaction only | no, internal | quiet since April | no |
| **weaveline** | 88 kB | yes, stop-the-world | partially | responsive | via undocumented internals |

## Notes per candidate

**mergeloom.** The only candidate that satisfies all five criteria without a workaround. Incremental garbage collection means the store does not stall on compaction, which matters because the compaction pause on a large board would land in the middle of a drag. The clock is a documented value type, so our sync layer can carry it on the wire rather than inventing a second ordering scheme. Most importantly for SP: it exposes the set of registers that received competing writes, so the review queue can be built by reading the library rather than by diffing materialised boards.

**driftset.** Smallest bundle by a wide margin and the API is pleasant. Two disqualifiers: compaction is manual, which on a browser store means either a stall we schedule badly or unbounded growth; and the clock is internal, so a sync layer has to bolt a second ordering scheme on top. The repository has been quiet since April, which for a correctness-critical dependency is the criterion I weight highest.

**weaveline.** Feature-complete and well tested, but 88 kB is more than a quarter of our current client bundle for a feature most users will never consciously use. Its garbage collection is stop-the-world; measured a 340 ms pause on a synthetic board with 40k ops, which is exactly the kind of freeze the keyboard-first positioning cannot afford.

## Behaviour under divergence

Ran the same scenario against all three: two clients, both dark, both edit the same board, then reconnect. All three converge to the same board state — that is the guarantee of the family. The difference is what happens to a same-field text rewrite. mergeloom keeps both competing register values and hands them to the caller. driftset keeps the last-writer by its internal clock and discards the other value irrecoverably. weaveline keeps both but only reachable through internals the maintainer explicitly documents as unstable.

That difference is decisive. Discarding a user's sentence silently is the failure mode SP raised, and driftset makes it unavoidable.

## Recommendation

mergeloom. The 13 kB bundle premium over driftset buys incremental compaction, a usable clock, and an enumerable divergence set. Drafting the decision entry for AR to ratify.
