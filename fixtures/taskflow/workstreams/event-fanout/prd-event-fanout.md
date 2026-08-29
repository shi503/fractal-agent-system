# PRD — EventFanout

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`
**Workstream ID:** `WS-2`
**Model tier:** `sonnet`
**Owner:** Feature Lead (RV)
**Depends on:** `[WS-1]`
**Status:** `COMPLETE`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

Turn a domain event into per-subscriber delivery rows and push them down the socket channel. The service owns three things the rest of NOVA depends on: the subscriber expansion query, the backpressure policy when a client stops draining, and the replay window a reconnecting client is entitled to.

**Source documents:**
- `wiki/raw/2026/08/2026-08-04-RV-websocket-spike-notes.md`
- `wiki/entities/websocket-fanout-service.md`

**Locked decisions:**
- `D-0001`: WebSocket fanout over server-sent events and long-polling.

## 2. Acceptance Criteria

- [ ] Exactly one delivery row per eligible subscriber per event, verified by an integration test.
- [ ] Reconnect replays the last 200 undelivered events with no duplicates.
- [ ] Backpressure drop path is covered by a test that asserts the drop is recorded, not silent.

## 3. Read / Write File Manifest

**Read only:** `lib/notifications/types.ts`, `decision-log/D-0001.md`
**Write / modify:** `lib/notifications/index.ts`
**Create:** `lib/notifications/fanout.ts`, `lib/notifications/channel.ts`, `lib/notifications/fanout.test.ts`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- Preference filtering beyond reading the stored preference row (WS-3 owns the surface).
- Vault sync piggybacking on the same channel (WS-5).

## 7. Blockers

**Blockers:** None
