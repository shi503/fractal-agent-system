---
okf_version: "0.2"
type: entity
entity_kind: system
title: "System — WebSocket Fanout Service"
tier: entities
initiative: NOVA
created: "2026-08-19"
updated: "2026-08-19"
created_by: RV
updated_by: RV
status: ACTIVE
aliases: ["fanout service", "the fanout", "notification channel"]
tags: [nova, system, notifications, websocket]
---

# WebSocket Fanout Service

**Canonical name:** WebSocket Fanout Service
**Kind:** System / internal service
**Owner:** RV (Rowan Vance)
**Shipped:** Phase 1, WS-2 (`FeatureLead-EventFanout`)

## Summary

The service that turns one domain event into per-subscriber deliveries and pushes them over the WebSocket channel. It is the only push transport in TaskFlow; the Phase 2 vault sync rides the same connection rather than opening its own.

## Responsibilities

1. **Subscriber expansion** — resolve a domain event to the set of users entitled to hear about it, filtered by stored preferences.
2. **Frame encoding** — serialise each event payload exactly once per event, not once per subscriber.
3. **Backpressure** — bound the per-socket outbound queue; drop and record rather than block the fanout loop.
4. **Replay** — serve a reconnecting client the last 200 undelivered events from its delivery cursor.

## Invariants

- Exactly one delivery row per eligible subscriber per event.
- A self-caused event never produces a delivery row for its own actor.
- A dropped frame is always recorded; a silent drop is a defect.
- Per-subscriber work stays under one millisecond, per the published resource envelope.

## Failure modes

| Mode | Trigger | Handling |
|---|---|---|
| Stalled consumer | client stops draining its socket | queue bounds, then drop-and-record |
| Proxy timeout | naive reverse proxy closes idle sockets | heartbeat frame; documented for self-hosters |
| Process restart | deploy or crash | client reconnects and replays from its cursor |
| Multi-process deployment | second app process holds a separate subscriber table | out of scope in Phase 1; needs a shared bus |

## Related

- `wiki/sources/notification-architecture-options.md` — why this design was chosen
- `decision-log/D-0001.md` — the decision that created this service
- `workstreams/event-fanout/prd-event-fanout.md` — the workstream that built it
