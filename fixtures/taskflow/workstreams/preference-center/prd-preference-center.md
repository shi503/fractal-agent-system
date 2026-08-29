# PRD — PreferenceCenter

**Blueprint:** `blueprints/BLUEPRINT-NOVA-P1-NotificationCore.yaml`
**Workstream ID:** `WS-3`
**Model tier:** `sonnet`
**Owner:** Feature Lead (SP)
**Depends on:** `[WS-1]`
**Status:** `NOT_STARTED`

> **FIXTURE.** Synthetic PRD for the TaskFlow NOVA fixture corpus. Nothing here describes real work.

---

## 1. Feature Overview

The user-facing settings surface for NOVA: category toggles, digest cadence, and quiet hours. The surface must render correctly for a user who has never saved anything, which is where the locked default policy shows up in the UI.

**Source documents:**
- `wiki/raw/2026/08/2026-08-08-SP-preference-center-sketch.md`
- `wiki/synthesis/notification-fatigue-principles.md`

**Locked decisions:**
- `D-0002`: Defaults are opt-in digests, not per-event pushes.

## 2. Acceptance Criteria

- [ ] Preference writes round-trip through a Zod-validated Server Action.
- [ ] A user with no stored row renders the documented defaults without writing a row.
- [ ] Every toggle is reachable by keyboard with a visible focus ring.

## 3. Read / Write File Manifest

**Read only:** `lib/notifications/types.ts`, `decision-log/D-0002.md`
**Write / modify:** `app/(dashboard)/settings/page.tsx`
**Create:** `app/(dashboard)/settings/notifications/page.tsx`, `app/(dashboard)/settings/notifications/actions.ts`, `components/notifications/preference-toggle.tsx`

## 4. CI Gate

```bash
npm run build && npx tsc --noEmit && npm run lint && npm run test:run
```

## 5. Session Protocol

Heartbeat to `PULSE.md` every ~30 min or at task boundaries. On completion generate `HANDOFF.md`. On block set `escalation_needed: true` and stop.

## 6. Out of Scope

- Server-side enforcement of quiet hours (WS-2 already filters at fanout time).
- Per-board preference overrides — backlog.

## 7. Blockers

**Blockers:** None
