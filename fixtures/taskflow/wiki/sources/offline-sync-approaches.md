---
okf_version: "0.2"
type: source
title: "Offline sync approaches — offline conflict resolution options"
tier: sources
initiative: NOVA
created: "2026-08-15"
updated: "2026-08-16"
created_by: RV
updated_by: AR
status: ACTIVE
source:
  - wiki/raw/2026/08/2026-08-12-AR-offline-vault-design-session.md
  - wiki/raw/2026/08/2026-08-14-RV-crdt-library-eval.md
tags: [nova, offline, sync, conflict, resolution, crdt]
---

# Offline sync approaches — offline conflict resolution options

Distilled from the offline vault design session and the library evaluation. This page is the input to D-0003. It is the canonical page for offline conflict resolution in NOVA — how an offline edit is reconciled, which offline conflict cases resolve automatically, and which offline conflict cases need a person.

## The three offline conflict resolution strategies considered

| Strategy | Who performs resolution | Offline edits survive? | Verdict |
|---|---|---|---|
| Last-write-wins on the server | server clock | no — the losing offline edit is discarded | rejected |
| Operational transform | pairwise transform functions | yes | rejected |
| Convergent replicated types | the data structure itself | yes | **recommended** |

### Last-write-wins

The cheapest offline conflict resolution policy and the worst one. Any offline edit that loses the clock comparison is destroyed with no record. For a tool whose whole offline promise is "keep working on the train", silently discarding the offline work is the one unacceptable outcome.

### Operational transform

Real offline conflict resolution, but the correctness burden sits in a pairwise transform function per op-type pair. TaskFlow has seven op types today, so the conflict surface grows quadratically with every op type added. The received wisdom that the transform functions are where the bugs live matched the room's experience.

### Convergent replicated types

Offline conflict resolution by construction: the merge is commutative, so two clients that saw the same ops in any order reach the same state. The cost is metadata — tombstones and clocks carried alongside the data — and the mitigation is a library with incremental garbage collection.

## What resolves automatically and what does not

This distinction is the practical heart of offline conflict resolution in NOVA.

**Resolves automatically (no human):** card moves, column reorders, label add and remove, assignee changes, due-date changes, archive and unarchive. These are set and register operations whose offline conflict semantics are already defined by the data type.

**Does not resolve automatically (needs a human):** a same-field text rewrite — two people retitle or rewrite the same card description while both are offline. No structure can decide intent. The structure will pick deterministically, and deterministic is not correct.

## The residue rule

Every offline conflict that cannot be resolved automatically must surface to a review queue with both candidate values intact. An offline conflict resolution scheme that silently discards a competing value fails the study's loudest requirement. This is why the library choice turned on whether the competing register values are enumerable through a supported API rather than through internals.

## Library implication

Only one evaluated candidate exposes the unresolved offline conflict set as a first-class API while also garbage-collecting incrementally and exposing its clock. See `wiki/raw/2026/08/2026-08-14-RV-crdt-library-eval.md` for the full comparison table.
