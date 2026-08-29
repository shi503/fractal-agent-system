# PRD — NotificationSchema

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`
**Workstream ID:** `WS-1`
**Model tier:** `opus`
**Owner:** Feature Lead (RV)
**Depends on:** `[]`
**Status:** `COMPLETE`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

NOVA needs one notification record shape that both the fanout service and the preference center agree on. This workstream lands that shape: a `Notification` row per logical event, a `NotificationDelivery` row per subscriber, a category enum, and an idempotency key contract every producer must honour so a retried producer never doubles a user's inbox.

**Source documents:**
- `wiki/sources/notification-architecture-options.md`
- `wiki/synthesis/nova-architecture-synthesis.md`

**Locked decisions:**
- `D-0001`: WebSocket fanout is the transport — the schema carries a delivery row per subscriber rather than a single broadcast row.
- `D-0002`: Preference defaults are opt-in digests — the schema stores an explicit default marker rather than inferring one.

## 2. Acceptance Criteria

- [ ] Prisma migration applies cleanly; `npx prisma generate` succeeds.
- [ ] Category enum covers all six product categories, each with a documented default state.
- [ ] Idempotency key format `{resource}-{id}-{event}` is documented and enforced by a unit test.
- [ ] `NotificationDelivery` carries a replay cursor column the fanout service can range-scan.

## 3. Read / Write File Manifest

**Read only:** `wiki/sources/notification-architecture-options.md`, `decision-log/D-0001.md`, `decision-log/D-0002.md`
**Write / modify:** `prisma/schema.prisma`
**Create:** `lib/notifications/types.ts`, `lib/notifications/idempotency.ts`, `lib/notifications/idempotency.test.ts`

## 4. CI Gate

```bash
npx prisma generate && npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- The fanout service itself (WS-2).
- Any preference UI (WS-3).
- Offline vault tables (Phase 2).

## 7. Blockers

**Blockers:** None
