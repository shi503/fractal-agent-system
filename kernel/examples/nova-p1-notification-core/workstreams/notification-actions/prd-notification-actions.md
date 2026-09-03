# PRD: notification-actions

**Blueprint:** `NOVA-P1-NotificationCore`
**Workstream id:** `notification-actions`
**Depends on:** `notification-schema` (evidence accepted)

---

## Feature overview

Expose list, unread-count, mark-read, and mark-all-read through Server Actions and RSC queries. Every call authenticates first, validates with Zod, and scopes to `session.user.id` + `session.user.teamId`. This workstream does not add pages or the unread badge.

**Guides (path only):**
- `docs/testing-patterns.md`
- `docs/frontend-dev-guide.md`

---

## Acceptance criteria

- [ ] `listNotifications` returns the current user's rows for the active team, newest first, excluding `deletedAt`
- [ ] `getUnreadCount` equals the number of those rows with `readAt == null`
- [ ] `markRead(id)` sets `readAt` only when `userId` matches the session; foreign ids are a user-safe error
- [ ] `markAllRead` sets `readAt` on all unread rows for the session user/team and is idempotent
- [ ] Unauthenticated callers redirect or receive a user-safe error — no Prisma messages
- [ ] Unit tests cover auth failure, Zod failure, success, and cross-user mark-read
- [ ] CI gate passes

---

## File manifest

### Read

- `prisma/schema.prisma` — Notification fields
- `lib/db.ts` — Prisma singleton
- `lib/auth.ts` — `auth()` session shape (`user.id`, `user.teamId`)
- `lib/actions/issues.ts` — canonical Server Action shape to copy

### Write

- none expected unless a shared validation helper already exists

### Create

- `lib/validations/notification.ts` — `MarkReadSchema` (`id: z.string().min(1)`)
- `lib/queries/notifications.ts` — `listNotifications`, `getUnreadCount` (RSC / server-only)
- `lib/actions/notifications.ts` — `markRead`, `markAllRead`
- `lib/actions/notifications.test.ts` — auth / Zod / success / cross-user cases

---

## CI gate

```text
npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run
```

Paste full output into evidence Layer 1.

---

## Out of scope

- Inbox page, nav badge, preference UI
- Emitting notifications from issue mutations (may be a follow-up; not this manifest)
- REST `/api/notifications` (agent HTTP can wrap these functions later)

---

## Blockers

- None — blocked only if `notification-schema` evidence is not accepted
