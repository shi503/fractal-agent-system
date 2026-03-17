# Workstream PRD: M1.3 — Team Invite Flow

**Epic:** M1 — Core Data Model + Auth
**Feature Lead model:** sonnet
**Dependencies:** `FeatureLead-AuthSetup` must be COMPLETE before starting
**Estimated scope:** 9 files created/modified

---

## Goal

Complete the team membership lifecycle: signup creates an Organization + Team with the user as `OWNER`, and existing team owners can invite new members via a shareable link. This workstream also stubs the dashboard shell (sidebar + layout) so subsequent milestones (M2 board UI) have a place to mount.

---

## Acceptance Criteria

1. New user signs up → `Organization`, `Team`, and `TeamMember` records are created with `role: OWNER` in the same transaction
2. Team owner can generate an invite link at `/settings` — the link is a URL with a secure token (stored in DB, expires in 7 days)
3. A logged-in user visiting the invite URL joins the team as `role: MEMBER`
4. RLS test: create two users in different teams; confirm `db.issue.findMany({ where: { teamId: teamA } })` returns empty for user from teamB (enforce in application layer — actual Supabase RLS is validated post-deploy)
5. `npm run test:run` passes — Server Action unit tests cover: auth check, Zod validation, success path, duplicate-member error
6. `npm run build` passes

---

## Scope

### Server Actions

**`lib/actions/users.ts`**:
- `createTeamOnSignup(userId: string, orgName: string, teamName: string)` — called from signup action; creates Org + Team + TeamMember in a Prisma transaction
- `generateInviteLink(teamId: string)` — creates an `Invite` record with a random token + 7-day expiry; returns the full invite URL
- `acceptInvite(token: string, userId: string)` — validates token, checks expiry, creates `TeamMember` record; errors if already a member or token expired

### Schema additions (coordinate with schema workstream if needed)

Add to `prisma/schema.prisma` (new model only — do not change existing models):
```prisma
model Invite {
  id        String    @id @default(cuid())
  token     String    @unique @default(cuid())
  teamId    String
  expiresAt DateTime
  usedAt    DateTime?
  createdAt DateTime  @default(now())
}
```
After adding: run `npx prisma generate`. Do NOT run `prisma migrate dev` — user configures DB separately.

### Queries

**`lib/queries/teams.ts`**:
- `getTeamMembers(teamId: string)` — returns members with user name/email
- `getTeamById(teamId: string)` — used in settings page

### Dashboard shell

**`app/(dashboard)/layout.tsx`** — authenticated layout:
- Check session via `auth()`; redirect to `/login` if no session
- Render a minimal sidebar stub (just a `<nav>` with team name and "Settings" link)
- `children` renders in the main content area
- Keep it simple — full sidebar is M3 scope

**`app/(dashboard)/settings/page.tsx`** — RSC team settings page:
- Display team name and list of current members (name, email, role)
- Show invite link generation button (renders `InviteForm`)
- If current user is not `OWNER`, hide the invite section

**`app/(dashboard)/settings/InviteForm.tsx`** — Client component:
- `"use client"` — handles button click + displays generated link
- Calls `generateInviteLink` Server Action on click
- Shows the resulting URL in a copyable text field
- No external API calls — Server Action only

**`app/(dashboard)/invite/[token]/page.tsx`** — RSC invite acceptance page:
- Load invite by token; show team name and "Join team" button
- On form submit: call `acceptInvite` Server Action
- If token invalid/expired: show error message
- If user not logged in: redirect to `/login?callbackUrl=/invite/[token]`

### Validation

**`lib/validations/user.ts`**:
```typescript
export const AcceptInviteSchema = z.object({
  token: z.string().min(1),
});
```

### Tests

**`lib/actions/users.test.ts`** — Vitest unit tests:
- Mock `db` using `vi.mock('@/lib/db')`
- Test `createTeamOnSignup`: auth present → creates org/team/member; auth missing → throws
- Test `generateInviteLink`: owner role → returns URL; non-owner → throws forbidden
- Test `acceptInvite`: valid token → creates member; expired token → returns error; duplicate → returns error

---

## File Manifest

### Read
- `lib/auth.ts` — `auth()` import pattern
- `prisma/schema.prisma` — existing models before adding `Invite`

### Write
- `lib/actions/users.ts`
- `lib/actions/users.test.ts`
- `lib/queries/teams.ts`
- `lib/validations/user.ts`
- `app/(dashboard)/layout.tsx`
- `app/(dashboard)/settings/page.tsx`
- `app/(dashboard)/settings/InviteForm.tsx`
- `app/(dashboard)/invite/[token]/page.tsx`
- `prisma/schema.prisma` — add `Invite` model only

### Do NOT touch
- `lib/auth.ts` — auth is M1.2's output; read only
- `lib/db.ts` — read only
- `app/(auth)/` routes — M1.2's output; read only

---

## Implementation Notes

### Transaction pattern for signup
```typescript
// lib/actions/users.ts
export async function createTeamOnSignup(userId: string, orgName: string, teamName: string) {
  return db.$transaction(async (tx) => {
    const org = await tx.organization.create({ data: { name: orgName } });
    const team = await tx.team.create({
      data: { name: teamName, organizationId: org.id },
    });
    await tx.teamMember.create({
      data: { teamId: team.id, userId, role: 'OWNER' },
    });
    return { org, team };
  });
}
```

### Invite token security
- Use `crypto.randomUUID()` for the token — do not use `cuid()` for security tokens
- Token is single-use: set `usedAt` on acceptance
- 7-day expiry enforced in `acceptInvite` before creating TeamMember

### teamId on session
The `auth()` session must include `user.teamId`. In M1.2, the session callback fetches `teamId` from the first `TeamMember` record. After `createTeamOnSignup` runs during signup, the session won't have `teamId` until the user re-authenticates. Handle this by calling `signIn` again at the end of the signup flow (already handled in M1.2 signup action).

### Security
- Never log invite tokens
- Sanitize all server-side errors before returning to client
- `acceptInvite` must verify the invite's `teamId` matches the team — prevent token reuse across teams

---

## Session Protocol

1. Read `.claude/CLAUDE.md` (server action patterns, component decision tree, testing patterns)
2. Read `.claude/fractal/STRATEGIST-taskflow.md` §4 (code quality constraints, data constraints)
3. Confirm `FeatureLead-AuthSetup` is COMPLETE — `lib/auth.ts` and login/signup pages must exist
4. Add `Invite` model to `prisma/schema.prisma`, run `npx prisma generate`
5. Implement Server Actions + queries first (business logic)
6. Implement UI pages and components
7. Write `lib/actions/users.test.ts` — all tests must pass with `npm run test:run`
8. Run `npx tsc --noEmit` and `npm run build` — both must pass
9. Emit `/handoff` when all acceptance criteria are met
