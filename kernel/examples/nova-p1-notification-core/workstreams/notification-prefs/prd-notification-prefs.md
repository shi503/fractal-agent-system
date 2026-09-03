# PRD: notification-prefs

**Blueprint:** `NOVA-P1-NotificationCore`
**Workstream id:** `notification-prefs`
**Depends on:** `notification-schema` (evidence accepted)

---

## Feature overview

Let a user turn off `ISSUE_ASSIGNED`, `ISSUE_COMMENTED`, or `STATUS_CHANGED` without deleting history. Settings render a per-category toggle grid. The write path that creates notifications (when it lands) must consult preferences; this workstream ships the guard used by that path.

May run in parallel with `notification-actions`.

**Guides (path only):**
- `docs/frontend-dev-guide.md`
- `docs/testing-patterns.md`

---

## Acceptance criteria

- [ ] `/settings/notifications` shows one toggle per category, bound to persisted `NotificationPreference` rows
- [ ] Missing rows default to enabled (all-on) without erroring
- [ ] Toggle persist + reload restores the saved value
- [ ] `shouldNotify({ userId, teamId, category })` returns false when that category is disabled
- [ ] CI gate passes

---

## File manifest

### Read

- `prisma/schema.prisma` — NotificationPreference
- `lib/db.ts`
- `lib/auth.ts`
- `app/(dashboard)/settings/page.tsx` — existing settings shell, if present

### Write

- `app/(dashboard)/settings/page.tsx` — add a link to notification preferences only if a settings page already exists

### Create

- `lib/queries/notification-preferences.ts` — `getPreferencesForUser`
- `lib/actions/notification-preferences.ts` — `updatePreference`
- `lib/notifications/should-notify.ts` — category guard
- `app/(dashboard)/settings/notifications/page.tsx` — RSC page
- `components/notifications/preference-grid.tsx` — client toggle grid
- `lib/actions/notification-preferences.test.ts`
- `lib/notifications/should-notify.test.ts`

---

## CI gate

```text
npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run
```

Paste full output into evidence Layer 1.

---

## Out of scope

- Inbox and unread badge (`notification-inbox`)
- List/mark-read actions (`notification-actions`)
- Email digest or mute-all
- Redesigning the rest of `/settings`

---

## Blockers

- None — blocked only if `notification-schema` evidence is not accepted
