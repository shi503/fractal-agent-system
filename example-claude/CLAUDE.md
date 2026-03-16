# CLAUDE.md — TaskFlow

> **This is a sample CLAUDE.md for the TaskFlow demo project** (a Linear-style kanban tracker).
> Copy this file into your project root and customize every section for your project.
> CLAUDE.md is the always-on context doc that grounds every Claude Code session.

---

## Product Identity

**TaskFlow** is a fast, keyboard-driven kanban project tracker for small teams (2–10 people).
It ships as a self-hosted open-source tool that matches Linear's interaction quality.

**Target user:** Engineering teams that want a self-hosted alternative to Linear with keyboard-first UX.

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| Components | shadcn/ui | latest |
| ORM | Prisma | 6.x |
| Database | Supabase Postgres | — |
| Auth | Auth.js (NextAuth) | 5.x |
| Deploy | Vercel | — |

---

## Commands

```bash
# Development
npm run dev              # Start dev server (localhost:3000)

# Build & typecheck
npm run build            # Next.js production build
npx tsc --noEmit         # TypeScript type-check (no output)

# Lint
npm run lint             # ESLint

# Test
npm test                 # Vitest
npm run test:e2e         # Playwright E2E

# Database
npx prisma generate      # Regenerate Prisma client after schema changes
npx prisma db push       # Push schema changes to Supabase (dev)
npx prisma migrate dev   # Create and apply migration (dev)
npx prisma studio        # Visual database browser
```

---

## Project Structure

```
app/
├── (auth)/              # Auth routes (login, signup, callback)
├── (dashboard)/         # Authenticated routes
│   ├── board/           # Kanban board view
│   ├── settings/        # User and team settings
│   └── layout.tsx       # Dashboard layout with sidebar
├── api/                 # Route Handlers (API endpoints)
├── layout.tsx           # Root layout
└── globals.css          # Tailwind base + design tokens

components/
├── board/               # Board-specific components (Board, Column, Card)
├── issues/              # Issue detail, editor, status badges
├── ui/                  # shadcn/ui primitives (Button, Dialog, Input, etc.)
└── command-palette/     # Cmd+K command palette

lib/
├── actions/             # Server Actions (mutations)
├── db.ts                # Prisma client singleton
├── auth.ts              # Auth.js configuration
└── utils.ts             # Shared utilities

prisma/
├── schema.prisma        # Data model (single source of truth)
└── migrations/          # Migration history
```

---

## Component Conventions

- **Server Components by default.** Only add `"use client"` when the component needs state, effects, or event handlers.
- **shadcn/ui for all primitives.** Button, Input, Dialog, DropdownMenu, etc. Never build custom equivalents.
- **Tailwind utility classes only.** No inline styles. No custom CSS unless Tailwind cannot express it.
- **One component per file.** Co-locate related hooks and types in the same directory.
- **Files under 300 lines.** Extract sub-components, hooks, or utilities when a file grows past this.

---

## State Management

- **Server Components** for initial data loading (database queries via Prisma in RSC)
- **`useOptimistic`** for all mutations that update the UI — the user never waits for the server
- **SWR** for client-side data that needs revalidation (e.g. real-time issue counts)
- **No client-side global store** (no Redux, Zustand, etc.) — Server Components + optimistic updates cover all cases

---

## API Conventions

- **Server Actions** for all mutations (create, update, delete). Colocate in `lib/actions/`.
- **Route Handlers** (`app/api/`) only for webhooks, external integrations, or endpoints that need HTTP method control.
- **Always validate inputs** with Zod schemas before database operations.
- **Return typed responses** — never return `any` from a Server Action.
- **Error handling:** Catch at the action level, return `{ error: string }` to the client. Never expose stack traces.

---

## Database Conventions

- **Prisma schema is the source of truth.** All data model changes start with `schema.prisma`.
- **Use `cuid()` for IDs** — not auto-increment integers.
- **Soft delete** for user-facing records (`deletedAt: DateTime?`). Hard delete only for truly ephemeral data.
- **RLS policies on all team-scoped tables** in Supabase. Every table with a `teamId` column must have a row-level security policy.
- **Timestamps on every table:** `createdAt`, `updatedAt` (auto-managed by Prisma).

---

## Forbidden Patterns

| Pattern | Why | Use Instead |
|---------|-----|-------------|
| `any` type | Disables type safety | `unknown` + type guards |
| `console.log` in committed code | Noise in production | Remove or use structured logging |
| Hardcoded secrets/API keys | Security risk | Environment variables (`process.env`) |
| `useEffect` for data fetching | Race conditions, loading states | Server Components or SWR |
| Inline styles | Breaks Tailwind consistency | Tailwind utility classes |
| Custom CSS | Drift from design system | Tailwind + shadcn/ui |
| Direct SQL queries | Bypasses Prisma type safety | Prisma client |
| Files over 300 lines | Reduces readability | Extract and refactor |
| `// @ts-ignore` or `// @ts-expect-error` | Hides real bugs | Fix the type error |
| Committing `.env` files | Exposes secrets | `.gitignore` + `.env.example` |
| `var` declarations | Function scoping bugs | `const` or `let` |
| Nested ternaries | Unreadable | `if/else` or early return |

---

## Design Principles

1. **Speed is the feature** — Every interaction < 100ms perceived latency. Optimistic updates everywhere. If the user can perceive a loading state, something is wrong.
2. **Keyboard-first, mouse-optional** — Power users never touch the mouse. `Cmd+K` for command palette. Single-key shortcuts for common actions (`C` = create, `X` = select).
3. **Opinionated defaults over configuration** — One board layout (kanban). One workflow (Backlog → Todo → In Progress → Done). Reduce decision fatigue.
4. **Visual density done right** — Show more information per pixel, like Linear. Not cluttered like Jira. Every element earns its space.

---

## Security

- Never log credentials, tokens, or PII (names, emails in debug logs)
- Environment variables for all secrets — never hardcode
- Sanitize all error messages shown to users — no stack traces in production
- RLS policies enforced at the database level, not just application code
- Auth.js middleware protects all `(dashboard)` routes

---

<!--
## Compliance (Optional)

Uncomment this section for projects with SOC2, BAA, or enterprise compliance requirements.
These constraints become part of the always-on context and flow into every agent session.

### Non-Negotiables
- **Supply chain:** Containers use approved base images only (e.g. Chainguard). No ad-hoc bases.
- **Sensitive data:** No credentials, PHI/PII, or document contents in logs, traces, errors, or metrics.
- **Config:** All environment-specific values come from env vars or approved secret managers. Zero hardcoded URLs, ports, or connection strings.
- **Observability:** Emit structured logs (JSON, ISO 8601 timestamps) with request/transaction ID propagation. Provide deep health checks (downstream reachability) and /metrics endpoints.
- **Deployability:** Startup runs idempotent DB migrations. Fail fast if migrations fail. Downgrades must be possible without destroying state.

### DO
- Use approved secret manager for all credentials
- Emit structured audit logs for security-relevant operations
- Run dependency audit (`npm audit`, `pip audit`, etc.) before merging
- Include compliance scan results in HANDOFF.md Verification Evidence table

### DON'T
- Log request/response bodies containing user data
- Introduce new third-party dependencies without security review
- Store sensitive data in client-side storage (localStorage, cookies without httpOnly)

### NEVER
- Commit `.env` files, credentials, or API keys
- Disable or weaken authentication/authorization checks
- Remove audit logging or observability instrumentation
- Use `// @ts-ignore` or equivalent to silence security-related type errors
-->

## Git Conventions

- **Branch naming:** `feat/short-description`, `fix/short-description`, `chore/short-description`
- **Commit messages:** Conventional Commits format (`feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`)
- **Never commit with a failing build** — `npm run build && npx tsc --noEmit` must pass
- **No `.env` files in git** — maintain `.env.example` with placeholder values
