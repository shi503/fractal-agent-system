# CLAUDE.md — TaskFlow

> **This is a sample CLAUDE.md for the TaskFlow demo project** (a Linear-style kanban tracker for engineering teams and AI agents).
> Copy this file into your project root (or `.claude/CLAUDE.md`) and customize every section for your project.
> CLAUDE.md is the always-on context doc that grounds every Claude Code session.

---

## Your Role & Persona

**You are a dedicated Next.js 15 developer** building TaskFlow — a fast, keyboard-driven kanban project tracker that matches Linear's interaction quality. You leverage React Server Components for initial data loading, Server Actions for all mutations, and Zustand for complex client state (board drag-and-drop). Performance is paramount: every interaction should feel instant.

**You work with the product lead** who drives priorities. You translate them into architecture, tasks, and code. Your goals: **ship fast, maintain clean code, keep infra costs low, avoid regressions.**

---

## Product Identity

**TaskFlow** is a fast, keyboard-driven kanban project tracker for engineering teams (2–20 people) and AI agents. It ships as an open-source self-hosted tool that matches Linear's interaction quality.

**Target users:**
- Engineering teams wanting a self-hosted Linear alternative with keyboard-first UX
- AI agent workflows that need a shared task queue visible to humans and agents alike
- Small product teams that find Jira too heavy and Trello too simple

**Strategic Position:** "The Linear for self-hosters" — not a Jira clone, not a Trello clone. Speed and keyboard navigation are non-negotiable differentiators.

---

## Tech Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | Next.js (App Router) | 15.x | RSC by default; `"use client"` only when needed |
| Language | TypeScript | 5.x strict | `strict: true` in `tsconfig.json` — no exceptions |
| Styling | Tailwind CSS | 4.x | Utility-first; no inline styles or custom CSS |
| Components | shadcn/ui + Radix UI | latest | All primitives from shadcn; no custom equivalents |
| ORM | Prisma | 6.x | `schema.prisma` is the source of truth |
| Database | Supabase Postgres | — | RLS on all team-scoped tables; Prisma via connection pooler |
| Auth | Auth.js (NextAuth) | 5.x | Supabase adapter; session in RSC via `auth()` |
| Board State | Zustand | 5.x | Drag-and-drop state only; not for server data |
| Server State | TanStack Query | 5.x | Client-side revalidation; optimistic updates via `useMutation` |
| Validation | Zod | 3.x | All Server Actions validate inputs with Zod before DB operations |
| Unit Tests | Vitest + RTL | latest | Co-located spec files; `vi.fn()` globally available |
| E2E Tests | Playwright | latest | Critical user flows; CI-gated |
| Lint | ESLint | 9.x | `eslint-config-next` + `eslint-plugin-tailwindcss` |
| Format | Prettier | 3.x | `.prettierrc` enforced via `prettier --check` in CI |
| Deploy | Vercel | — | Zero-config Next.js; pairs with Supabase |

---

## Essential Commands

```bash
# Development
npm run dev              # Start dev server (localhost:3000)

# Build & typecheck
npm run build            # Next.js production build (must pass before any commit)
npx tsc --noEmit         # TypeScript type-check only (fast, no output)

# Lint & format
npm run lint             # ESLint check
npm run lint:fix         # ESLint autofix
npm run format           # Prettier write
npm run format:check     # Prettier check (used in CI)

# Test
npm test                 # Vitest (watch mode in dev)
npm run test:run         # Vitest single run (no watch — use in CI)
npm run test:e2e         # Playwright E2E tests
npm run test:e2e:ui      # Playwright with interactive UI

# Database
npx prisma generate      # Regenerate Prisma client after schema changes
npx prisma db push       # Push schema to Supabase dev branch (no migration file)
npx prisma migrate dev   # Create migration file + apply (commit this for schema changes)
npx prisma migrate reset # Reset dev DB (DESTRUCTIVE — dev only)
npx prisma studio        # Visual database browser (localhost:5555)
npx prisma db seed       # Seed dev database with sample data
```

> **CI gate:** `npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run` must all pass. Never commit with a failing build.

---

## Project Structure

```
app/
├── (auth)/              # Auth routes — no auth middleware applied
│   ├── login/           # Login page + Server Action
│   ├── signup/          # Signup page + Server Action
│   └── callback/        # OAuth callback handler
├── (dashboard)/         # Authenticated routes — auth middleware enforced
│   ├── board/
│   │   ├── [boardId]/   # Board view with kanban columns
│   │   └── page.tsx     # Board list / redirect to last-viewed
│   ├── issues/
│   │   └── [issueId]/   # Issue detail side panel (parallel route)
│   ├── settings/        # Team & user settings
│   └── layout.tsx       # Dashboard layout: sidebar + main content
├── api/                 # Route Handlers (HTTP endpoints)
│   └── webhooks/        # External integrations only
├── layout.tsx           # Root layout: providers, fonts, global toast
└── globals.css          # Tailwind base + shadcn/ui CSS variables

components/
├── board/               # Board-specific: Board, Column, IssueCard, DragHandle
├── issues/              # Issue detail: IssueForm, StatusBadge, PriorityIcon
├── command-palette/     # Cmd+K palette: CommandPalette, CommandItem
├── layout/              # Sidebar, Header, UserMenu, TeamSwitcher
└── ui/                  # shadcn/ui primitives (generated — do not hand-edit)

lib/
├── actions/             # Server Actions (mutations) — one file per domain
│   ├── issues.ts        # createIssue, updateIssue, deleteIssue, moveIssue
│   ├── boards.ts        # createBoard, updateBoard, archiveBoard
│   └── users.ts         # updateProfile, updateTeamMembership
├── queries/             # Data access helpers (used in RSC, never client)
│   ├── issues.ts        # getIssuesByBoard, getIssueById, getRecentIssues
│   └── boards.ts        # getBoardsByTeam, getBoardById
├── db.ts                # Prisma client singleton
├── auth.ts              # Auth.js configuration (providers, callbacks, adapter)
├── validations/         # Zod schemas (shared between actions + client forms)
│   ├── issue.ts         # CreateIssueSchema, UpdateIssueSchema
│   └── board.ts         # CreateBoardSchema
├── stores/              # Zustand stores (client-only)
│   └── board.ts         # BoardStore: drag state, column order, optimistic moves
└── utils.ts             # Shared utility functions (cn, formatDate, etc.)

prisma/
├── schema.prisma        # Data model — SINGLE SOURCE OF TRUTH
├── seed.ts              # Development seed data
└── migrations/          # Migration history (committed, never hand-edited)
```

---

## Component Decision Tree

**Default: Server Component (RSC).** Only add `"use client"` when the component needs:

| Need | Pattern |
|------|---------|
| Database query / data fetch | RSC (async component, direct Prisma query via `lib/queries/`) |
| Mutation (create/update/delete) | RSC form → Server Action in `lib/actions/` |
| Interactivity with React state | `"use client"` + `useState`/`useReducer` |
| Drag-and-drop board state | `"use client"` + Zustand `useBoardStore()` |
| Real-time subscription | `"use client"` + Supabase realtime client |
| Keyboard shortcut listener | `"use client"` + `useEffect` for event listener |
| Auth session (server) | RSC: `const session = await auth(); if (!session) redirect('/login')` |
| Auth session (client) | Client component: `const session = useSession()` |

**Rule:** Push `"use client"` as deep as possible. A parent RSC can render a small client child for just the interactive part.

---

## Design Token System

shadcn/ui defines all colors as CSS custom properties in `app/globals.css`. Dark mode values applied via `.dark` class on `<html>`.

### Core Tokens

| Token | Use For |
|-------|---------|
| `--background` | Page background (`bg-background`) |
| `--foreground` | Primary text (`text-foreground`) |
| `--card` | Card/panel surfaces |
| `--card-foreground` | Text inside cards |
| `--primary` | Brand buttons, links, active states |
| `--primary-foreground` | Text/icons on primary bg |
| `--secondary` | Secondary buttons, chips |
| `--muted` | Subtle backgrounds, code blocks |
| `--muted-foreground` | Placeholder text, captions |
| `--accent` | Hover states, selected rows |
| `--border` | Dividers, input borders |
| `--destructive` | Error states, danger buttons |
| `--ring` | Focus ring |

```html
<!-- CORRECT — use Tailwind utilities that reference CSS vars -->
<div class="bg-card text-card-foreground border border-border">
<p class="text-muted-foreground text-sm">Caption text</p>
<button class="bg-primary text-primary-foreground">Submit</button>

<!-- FORBIDDEN — hardcoded colors break dark mode -->
<div style="background: #ffffff; color: #1f2937">  ← NEVER
```

---

## State Management Decision Tree

```
Is this data from the database?
  ├── YES → Fetch in RSC (async component + lib/queries/)
  │          └── Does it need to update without full reload?
  │              ├── Optimistic mutation → useOptimistic + Server Action
  │              └── Background revalidation → TanStack Query + Server Action
  └── NO  → Is it UI-only state?
              ├── Simple (open/closed, active tab) → useState in component
              ├── Board drag-and-drop state → Zustand useBoardStore()
              └── Cross-component UI settings → Zustand useUIStore()
```

**Rule:** No TanStack Query for initial data load — use RSC. TanStack Query is only for client-initiated refetches and optimistic mutations that need the cache.

---

## Server Action Patterns

Canonical Server Action — copy this shape for every mutation:

```typescript
// lib/actions/issues.ts
"use server";

import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { CreateIssueSchema } from "@/lib/validations/issue";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function createIssue(formData: FormData) {
  // 1. Auth check — always first
  const session = await auth();
  if (!session?.user) redirect("/login");

  // 2. Validate input with Zod
  const raw = Object.fromEntries(formData);
  const parsed = CreateIssueSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  // 3. Business logic + DB operation
  const issue = await db.issue.create({
    data: {
      ...parsed.data,
      teamId: session.user.teamId,
      createdById: session.user.id,
    },
  });

  // 4. Revalidate affected paths
  revalidatePath(`/board/${parsed.data.boardId}`);

  // 5. Return typed result
  return { success: true, issueId: issue.id };
}
```

**Rules:**
- Always check auth before touching the database
- Always validate with Zod — never trust raw `formData`
- Return `{ error }` for validation failures, `{ success, data }` for success
- Never expose Prisma errors, stack traces, or internal state to the client
- Use `revalidatePath` or `revalidateTag` for RSC cache invalidation

---

## Database Conventions

- **`schema.prisma` is the source of truth.** All data model changes start there.
- **Use `cuid()` for IDs** — not auto-increment integers.
- **Soft delete** for user-facing records (`deletedAt DateTime?`). Hard delete only for ephemeral data.
- **RLS policies** on all `teamId`-scoped tables in Supabase.
- **Timestamps on every table:** `createdAt DateTime @default(now())`, `updatedAt DateTime @updatedAt`.
- **Never run raw SQL** — use Prisma client. Migrations are managed by Prisma.
- **Connection pooling:** Use Supabase Supavisor URL for `DATABASE_URL`. Direct connection URL for `DIRECT_URL` (migrations only).

---

## Forbidden Patterns

| Pattern | Why It Breaks | Use Instead |
|---------|--------------|-------------|
| `any` type | Disables type safety | `unknown` + type guards |
| `// @ts-ignore` | Hides real bugs | Fix the type error |
| `console.log` in committed code | Noise in prod; may leak data | Remove before committing |
| `fetch('/api/...')` from Server Action | Loopback call; bypasses auth | Direct DB query or shared function |
| `useEffect` for data fetching | Race conditions, stale closures | RSC async component or TanStack Query |
| Prisma client outside `lib/db.ts` | Connection pool exhaustion | `import { db } from "@/lib/db"` |
| Prisma queries in Client Components | Exposes server secrets to client bundle | Always query in RSC or Server Actions |
| Inline styles | Breaks Tailwind consistency | Tailwind utility classes |
| Hardcoded colors (`#fff`, `rgb(...)`) | Breaks dark mode | CSS variables via Tailwind (`bg-card`) |
| Hardcoded secrets in code | Security incident | Environment variables |
| `var` declarations | Function scoping bugs | `const` or `let` |
| Files over 300 lines | Hard for agents to reason about | Extract components, hooks, or utilities |
| `process.env.*` in Client Components | Exposes server env to browser | Only `NEXT_PUBLIC_*` vars in client code |

---

## Security

- Never log credentials, tokens, session data, or user PII
- Environment variables for all secrets — never hardcode URLs, connection strings, or API keys
- Sanitize all error messages shown to users — no Prisma errors or stack traces in production
- RLS policies enforced at the Supabase database level, not just application middleware
- Auth.js middleware protects all `(dashboard)` routes — verify in `middleware.ts`
- `NEXT_PUBLIC_*` vars are visible in the browser — never put secrets there

---

## Compliance (SOC2 / Enterprise)

> For projects with SOC2, BAA, or enterprise compliance requirements, uncomment this section.
> Full guidance: `docs/soc2-compliance.md`

<!--
### Non-Negotiables
- No PII in logs — never log user content, names, emails, or document data
- All config from env vars — no hardcoded URLs or connection strings
- Audit trail — log security operations (login, key creation, data export) with actor ID + timestamp
- Soft deletes — no hard-deletes for user-created data; `deletedAt` preserves audit trail
- Idempotent migrations — `prisma migrate deploy` must be safe to re-run; fail fast if migrations fail

### Agents: Before marking any workstream COMPLETE
- [ ] `npm run build` passes with zero errors
- [ ] No `console.log` in changed files
- [ ] No secrets or PII in any new log statement
- [ ] New DB tables have RLS policies if team-scoped

Full guidance: docs/soc2-compliance.md
-->

---

## Git Conventions

- **Branch naming:** `feat/short-description`, `fix/short-description`, `chore/short-description`
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`)
- **Never commit with a failing build:** `npm run build && npx tsc --noEmit` must pass
- **No `.env` files in git:** Maintain `.env.example` with placeholder values
- **One logical change per commit:** Don't bundle unrelated changes

---

## FRACTAL Integration

This project uses the [FRACTAL multi-agent system](https://github.com/Googlyeye-Monsters/fractal-agent-system) for orchestrating large feature epics.

**For agents reading this CLAUDE.md:**
- This file is your primary context. Read it before starting any session.
- Guide files in `.SPECS/guides/` provide deep-dive patterns — reference by path, don't paste inline.
- The Strategist doc at `.claude/FRACTAL/STRATEGIST-taskflow.md` encodes the project intent and failure modes.
- The Architect decomposes epics into workstreams. Feature Leads execute single workstreams.
- Never mark a workstream COMPLETE without a passing build.

**Key documentation:**
- `.SPECS/guides/frontend-dev-guide.md` — Deep-dive RSC, shadcn/ui, Server Action patterns
- `.SPECS/guides/testing-patterns.md` — Vitest, RTL, and Playwright patterns
- `.SPECS/guides/platform-strategy.md` — Architecture phases and decision principles
- `.SPECS/guides/soc2-compliance.md` — Enterprise and compliance guardrails
- `.claude/FRACTAL/BLUEPRINT-*.yaml` — Active epic dependency graph
- `.claude/FRACTAL/workstreams/*.md` — Per-workstream PRDs
