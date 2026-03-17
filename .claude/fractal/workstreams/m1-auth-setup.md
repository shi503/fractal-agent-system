# Workstream PRD: M1.2 — Auth Setup

**Epic:** M1 — Core Data Model + Auth
**Feature Lead model:** sonnet
**Dependencies:** `FeatureLead-SchemaPrisma` must be COMPLETE before starting
**Estimated scope:** 8 files created/modified

---

## Goal

Configure Auth.js (NextAuth) v5 with the Supabase Postgres adapter and a credentials provider. The session must be accessible via `auth()` in all RSC components under `(dashboard)`. Unauthenticated users are redirected to `/login`. The session must carry `user.id`, `user.teamId`, and `user.email`.

---

## Acceptance Criteria

1. `npx tsc --noEmit` passes — no auth-related type errors
2. `auth()` called in an RSC under `app/(dashboard)/` returns a typed session object with `user.id`, `user.teamId`, `user.email`
3. Navigating to `/board` (unauthenticated) redirects to `/login`
4. The login form accepts email + password; invalid credentials return a user-facing error (no stack traces, no Prisma errors)
5. The signup flow creates a `User` record via the Prisma adapter — no duplicate email allowed (show user-facing error)
6. `npm run build` passes (no type errors, no missing imports)

---

## Scope

### Auth configuration

**`lib/auth.ts`** — Auth.js v5 config:
- Use `@auth/prisma-adapter` with the `db` singleton from `lib/db.ts`
- Credentials provider: email + password (bcrypt hash stored on User — add `passwordHash String?` to schema if not present; coordinate with schema workstream if needed)
- Extend the session to include `user.teamId` via the `session` callback
- Export `{ auth, signIn, signOut, handlers }` — this is the Auth.js v5 pattern

**`app/api/auth/[...nextauth]/route.ts`** — mount the Auth.js handlers

**`middleware.ts`** — protect `(dashboard)` routes:
- Any path NOT matching `/(auth)/*` or `/api/auth/*` requires an active session
- Redirect to `/login` if no session

### Login page

**`app/(auth)/login/page.tsx`** — RSC login page:
- shadcn/ui `Card`, `Input`, `Button` components
- Form submits to a Server Action
- Display validation errors inline (no page reload)

**`app/(auth)/login/actions.ts`** — Server Action:
- Validate with `LoginSchema` (Zod)
- Call `signIn("credentials", ...)` from Auth.js
- Return `{ error: string }` on failure — never expose Prisma errors or stack traces

**`lib/validations/auth.ts`** — Zod schemas:
```typescript
export const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export const SignupSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  password: z.string().min(8).max(72), // bcrypt max
});
```

### Signup page

**`app/(auth)/signup/page.tsx`** — RSC signup page (same visual pattern as login)

**`app/(auth)/signup/actions.ts`** — `createAccount` Server Action:
- Validate with `SignupSchema`
- Hash password with `bcryptjs`
- Create `User` record via `db.user.create(...)`
- Immediately sign in after creation (`signIn("credentials", ...)`)
- On duplicate email: return `{ error: "An account with this email already exists" }`

---

## File Manifest

### Read
- `prisma/schema.prisma` — to confirm User model fields
- `lib/db.ts` — Prisma singleton import

### Write
- `lib/auth.ts`
- `lib/validations/auth.ts`
- `middleware.ts`
- `app/api/auth/[...nextauth]/route.ts`
- `app/(auth)/login/page.tsx`
- `app/(auth)/login/actions.ts`
- `app/(auth)/signup/page.tsx`
- `app/(auth)/signup/actions.ts`

### Install (if not already present)
- `npm install bcryptjs` + `npm install -D @types/bcryptjs`

### Do NOT touch
- `prisma/schema.prisma` — if `passwordHash` field is missing, add it ONLY to the User model and run `npx prisma generate`. Do not change any other model.
- `lib/db.ts` — read-only in this workstream
- Any `(dashboard)` route files — those are M1.3's scope

---

## Implementation Notes

### Auth.js v5 session extension pattern
```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import { PrismaAdapter } from '@auth/prisma-adapter';
import Credentials from 'next-auth/providers/credentials';
import { db } from '@/lib/db';

export const { auth, signIn, signOut, handlers } = NextAuth({
  adapter: PrismaAdapter(db),
  session: { strategy: 'jwt' },
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      async authorize(credentials) {
        // validate with Zod, fetch user, compare bcrypt hash
        // return user object or null
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      if (token.sub) {
        session.user.id = token.sub;
        // fetch teamId from DB and attach
      }
      return session;
    },
    async jwt({ token, user }) {
      if (user) token.sub = user.id;
      return token;
    },
  },
});
```

### TypeScript session augmentation
Create `types/next-auth.d.ts`:
```typescript
import { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      teamId: string | null;
    } & DefaultSession['user'];
  }
}
```

### Security rules (non-negotiable)
- Never log `credentials.password` or any token value
- Never return Prisma errors to the client — catch and return generic messages
- Sanitize all user-facing error messages: no stack traces, no field names from DB
- No PHI in any log statement, even in `development` mode

---

## Session Protocol

1. Read `.claude/CLAUDE.md` (server action patterns, security section) before starting
2. Read `.claude/fractal/STRATEGIST-taskflow.md` §4 and §5 (FM-2: PHI surfaces, security constraints)
3. Confirm `FeatureLead-SchemaPrisma` is COMPLETE — check `prisma/schema.prisma` exists with User model
4. Install `bcryptjs` + types
5. Implement in order: `lib/auth.ts` → `middleware.ts` → route handler → login → signup
6. Run `npx tsc --noEmit` — fix all errors before emitting handoff
7. Run `npm run build` — must pass
8. Emit `/handoff` when all acceptance criteria are met
