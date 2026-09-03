# PRD: notification-inbox

**Blueprint:** `NOVA-P1-NotificationCore`
**Workstream id:** `notification-inbox`
**Depends on:** `notification-actions` (evidence accepted)

---

## Feature overview

Ship the user-visible inbox and the nav unread badge. The page lists the current user's notifications; unread rows are visually distinct; mark-read (single and all) updates the list and the badge without a full page reload. Badge count comes from `getUnreadCount` / a small Zustand store — not a second query language.

Does not wait on `notification-prefs`.

**Guides (path only):**
- `docs/frontend-dev-guide.md`
- `docs/testing-patterns.md`

---

## Acceptance criteria

- [ ] `/inbox` is reachable from the dashboard shell and lists notifications newest first
- [ ] Unread rows are visually distinct; read rows show a read state
- [ ] Mark-read on a row and mark-all-read both call the existing Server Actions
- [ ] Nav badge shows `unreadCount` and is hidden when the count is 0
- [ ] After mark-read, the badge decrements without requiring a full reload
- [ ] Unauthenticated visit to `/inbox` redirects to login
- [ ] CI gate passes

---

## File manifest

### Read

- `lib/queries/notifications.ts`
- `lib/actions/notifications.ts`
- `lib/auth.ts`
- `app/(dashboard)/layout.tsx` — where the badge mounts
- `components/layout/` — existing sidebar / header primitives

### Write

- `app/(dashboard)/layout.tsx` — mount the unread badge in the existing nav
- Sidebar / header component that already renders nav items — add the badge slot only

### Create

- `app/(dashboard)/inbox/page.tsx` — RSC list
- `components/notifications/inbox-list.tsx` — client list + mark-read controls
- `lib/stores/notifications.ts` — Zustand: `unreadCount`, `setUnreadCount`, `decrement`
- `components/notifications/unread-badge.tsx` — badge bound to the store
- `components/notifications/inbox-list.test.tsx` — unread styling + mark-read call
- `lib/stores/notifications.test.ts` — increment / decrement / hide-at-zero

---

## CI gate

```text
npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run
```

Paste full output into evidence Layer 1.

---

## Out of scope

- Preference toggles (`notification-prefs`)
- New Prisma models or migrations
- Realtime push into the badge
- Email or toast notifications
- Keyboard shortcuts beyond native focus (Cmd+K integration is a later epic)

---

## Blockers

- None — blocked only if `notification-actions` evidence is not accepted
