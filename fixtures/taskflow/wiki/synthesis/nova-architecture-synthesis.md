---
okf_version: "0.2"
type: synthesis
title: "NOVA architecture synthesis"
tier: synthesis
initiative: NOVA
created: "2026-08-20"
updated: "2026-08-22"
created_by: AR
updated_by: AR
status: ACTIVE
source:
  - wiki/sources/notification-architecture-options.md
  - wiki/sources/notification-user-research.md
  - wiki/sources/selfhost-resource-envelope.md
  - wiki/sources/offline-sync-approaches.md
tags: [nova, synthesis, architecture, notifications, vault]
---

# NOVA architecture synthesis

The cross-cutting read on NOVA after Phase 1 landed and Phase 2 opened. Four source pages fed this; each claim below points back at one of them.

## 1. NOVA is one channel, not two features

The notification work and the offline vault work look like separate features and were scoped as separate phases, but they resolved to the same primitive: a single bidirectional connection per client. That is the through-line of `wiki/sources/notification-architecture-options.md` — the transport was chosen partly on its Phase 2 reuse, not only on its Phase 1 merits. Had Phase 1 chosen a one-directional transport, Phase 2 would have had to introduce a second one, and a self-hoster would be configuring two proxy timeouts instead of one.

The lesson generalises: when two phases are separated by time but share a client, choose the Phase 1 primitive with the Phase 2 requirement already in hand.

## 2. The constraint that shaped everything is a small box

`wiki/sources/selfhost-resource-envelope.md` publishes roughly 320 MB of app-process headroom on the reference deployment. Nearly every non-obvious design choice in NOVA traces to that number: subscriber-table entries stay small, per-event work is bounded per subscriber, the server keeps ops rather than materialised documents, and the browser store is bounded with a deterministic eviction policy. None of these would be the natural choice on a machine with room to spare.

The published envelope also does something subtler: it converts an argument about taste into an argument about a number. Three separate design debates ended by pointing at the same table.

## 3. Quiet by default is a product position, not a setting

`wiki/sources/notification-user-research.md` found that users do not tune volume — they flip between everything-on and everything-off. That finding turned what looked like a settings question into a positioning question, and it is the reason the starting posture is quiet with a roll-up as the primary reading surface. See `wiki/synthesis/notification-fatigue-principles.md` for the principles this hardened into.

## 4. The residue rule is the real vault requirement

`wiki/sources/offline-sync-approaches.md` establishes that the merge settles structure but not intent, and that the small residue must surface to a person with both candidate values intact. This single requirement drove the library choice, created a whole workstream (the review queue), and is the one place where a wrong call would destroy user work rather than merely annoy.

## 5. What the three phases actually sequence

Phase 1 built the channel and the record shape. Phase 2 rides that channel with a bounded local store and a merge. Phase 3 measures the result against the published envelope and audits the surfaces. The sequence is not arbitrary: each phase produces the constraint the next one is checked against.

---

## See also

Documents this page was built from or that continue its argument directly.

- `wiki/sources/notification-architecture-options.md` — the transport comparison behind §1
- `wiki/sources/selfhost-resource-envelope.md` — the budget behind §2
- `wiki/sources/notification-user-research.md` — the study behind §3
- `wiki/sources/offline-sync-approaches.md` — the merge analysis behind §4
- `wiki/synthesis/notification-fatigue-principles.md` — the product principles derived from §3

## Backlinks

Documents that reference this page.

- `blueprints/BLUEPRINT-NOVA-P2-OfflineVault.yaml` — cites this page in its context block
- `decision-log/D-0001.md` — cross-references this synthesis
- `workstreams/notification-schema/prd-notification-schema.md` — source document
- `workstreams/conflict-resolution-ux/prd-conflict-resolution-ux.md` — source document

## Related (semantic)

Neighbours by subject rather than by citation — surfaced by retrieval, not asserted by an author.

- `wiki/entities/websocket-fanout-service.md` — the system this architecture instantiates
- `wiki/raw/2026/08/2026-08-12-AR-offline-vault-design-session.md` — the argument that produced §4
- `wiki/raw/2026/08/2026-08-03-AR-notification-options-whiteboard.md` — the argument that produced §1
- `wiki/entities/alex-rivera.md` — the author entity
