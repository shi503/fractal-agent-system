# PRD: notification-schema

**Blueprint:** `NOVA-P1-NotificationCore`
**Workstream id:** `notification-schema`
**Depends on:** none

---

## Feature overview

Define the TaskFlow notification data model. Later workstreams read and write these tables; they must be stable, team-scoped, and free of PHI columns. This workstream does not add UI or Server Actions.

**Guides (path only):**
- `docs/testing-patterns.md`
- `prisma/schema.prisma`

---

## Acceptance criteria

- [ ] `npx prisma validate` passes
- [ ] `npx prisma generate` succeeds
- [ ] `Notification` and `NotificationPreference` exist with `teamId`, timestamps, and soft-delete (`deletedAt`)
- [ ] `Notification.category` is an enum: `ISSUE_ASSIGNED`, `ISSUE_COMMENTED`, `STATUS_CHANGED`
- [ ] Seed creates ≥1 unread and ≥1 read notification for the demo user
- [ ] CI gate passes

---

## File manifest

### Read

- `prisma/schema.prisma` — existing models; follow `cuid()`, `teamId`, timestamp conventions
- `prisma/seed.ts` — extend, do not replace, existing org/team/board seed
- `lib/db.ts` — confirm singleton import path only

### Write

- `prisma/schema.prisma` — add models and enum only; do not reshape User/Issue/Team
- `prisma/seed.ts` — append notification + preference rows for the existing demo user
- `.env.example` — only if a new variable is required (none expected)

### Create

- `prisma/migrations/` — one migration for the new models (do not hand-edit SQL after generate)

---

## CI gate

```text
npx prisma validate && npx prisma generate && npx tsc --noEmit && npm run lint && npm run format:check
```

Paste full output into evidence Layer 1. Self-assessment is not evidence.

---

## Out of scope

- Server Actions, REST routes, or UI
- Email / push providers
- Realtime subscriptions
- Changing Issue or Comment write paths to emit notifications (later workstreams)

---

## Blockers

- None
