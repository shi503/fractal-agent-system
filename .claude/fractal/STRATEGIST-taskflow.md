# STRATEGIST-taskflow.md
**Project:** TaskFlow
**Mode:** A — Full Discovery
**Generated:** 2026-03-16
**Author:** Strategist (FRACTAL Tier 0)

> This document encodes WHY TaskFlow exists and WHAT good looks like.
> The Architect (Tier 1) reads this before decomposing any epic.
> Do not edit this document directly — run the Strategist interview to update it.

---

## 0. What Right Looks Like

Competitive benchmarks anchoring all Layer 3/4 evaluations at milestone boundaries.

| Capability Area | Benchmark Product | What They Do Right | Target |
|----------------|-------------------|--------------------|--------|
| **Core Workflow** | Linear | Issues feel instant — optimistic updates everywhere, no page reloads on mutations, drag feels native, keyboard shortcuts for every action. AI/agent workflows are natural participants, not an afterthought. | 5/5 |
| **Data Management** | Linear | Fast filtering by assignee/label/priority, bulk status transitions, clean label management. State changes feel immediate. | 4/5 |
| **Developer / Agent UX** | Linear API | REST API is clean, auth is straightforward, error messages are actionable. FRACTAL agents can read/write issues without a browser session. | 3/5 at launch → 5/5 by Phase 2 |
| **Real-time / Collaboration** | N/A | Not a Phase 1 priority. Optimistic UI covers single-user freshness. Supabase realtime deferred to Phase 2. | 1/5 |
| **Navigation & Discovery** | Linear | Cmd+K palette surfaces every action. Keyboard shortcuts cover 100% of the core workflow. No mouse required for power users. Tab order is logical; focus trapping in modals. | 5/5 |
| **Onboarding & First Run** | Supabase | Technical users (engineering leads) can self-host via Docker Compose. Env var reference is clear. Seed data included. Target: from `git clone` to first board in under 15 minutes. | 3/5 |

---

## 1. Project Mandate

TaskFlow is a **self-hosted, open-source kanban platform** built for healthcare engineering teams and AI agent workflows. It delivers Linear-quality interaction speed with a clean REST API that makes FRACTAL AI agents first-class team members alongside humans.

**Phase 1** ships the fastest self-hosted Linear alternative: keyboard-first board, full issue lifecycle, and a REST API FRACTAL agents can use on day one.

**Phase 2** makes agents native team members: API keys, workflow templates for healthcare ops (prior auth queues, CDI worklists, appeals backlogs), AI issue triage, and automations.

**Phase 3** delivers the compliance and analytics layer healthcare organizations need to replace Jira and Asana for regulated workflows: HIPAA BAA tier, audit trail export, EHR webhook integrations, SSO/SCIM.

**Strategic position:** "The Linear for self-hosters" — not a Jira clone, not a Trello clone. Speed, keyboard navigation, and agent-native APIs are non-negotiable differentiators in all three phases.

**Agent teams operating on this mandate should optimize for:** interaction speed, API ergonomics for FRACTAL agents, healthcare-safe defaults, and self-hostability. Every architectural decision must be evaluated against these four axes before shipping.

---

## 2. Core Intent & Guiding Principles

Priority-ordered. In conflicts, higher principles win.

| # | Principle | What It Means in Practice |
|---|-----------|--------------------------|
| 1 | **Speed is non-negotiable** | Every user-visible mutation uses optimistic updates. No page reloads. Interactions must feel instant vs. Linear. If it feels slower, it ships with a regression. |
| 2 | **Agents are first-class** | Every feature accessible to humans must be accessible to FRACTAL agents via the REST API. No "UI-only" data paths. Agent attribution (`source`, `agentId`) stamped on all agent mutations. |
| 3 | **Healthcare-safe by default** | No PHI in logs, URLs, error messages, analytics events, or browser storage — ever. This is not a Phase 3 concern; it is a Day 1 invariant. |
| 4 | **Keyboard-first UX** | Every action reachable from keyboard. Cmd+K palette is a P0 feature, not a nice-to-have. Tab order is logical. Focus trapping in all modals (Radix UI). |
| 5 | **Self-hostable always** | Open-source core must remain deployable behind any firewall without Vercel or Supabase Cloud. No cloud-only features in the core codebase. |
| 6 | **Keep infra costs low** | RSC by default, Server Actions for mutations, Supabase connection pooling. No unnecessary client-side JS. No custom infrastructure unless absolutely required. |

---

## 3. Definition of Done (Phase 1)

All of the following must be true before Phase 1 is considered shipped:

- [ ] **CI gate passes end-to-end:** `npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run` — all green, no exceptions
- [ ] **Core board E2E:** Playwright test covers: create board → add issues → drag issue across columns → close issue → verify state. Must pass on clean install.
- [ ] **FRACTAL agent integration:** A FRACTAL agent can authenticate via API key and execute: `GET /api/issues`, `POST /api/issues`, `PATCH /api/issues/:id`, `POST /api/issues/:id/comments` — without a browser session or UI interaction.
- [ ] **Self-host docs complete:** Docker Compose setup, full environment variable reference, and database seed script. A new engineer with no prior context can deploy in under 15 minutes.
- [ ] **No PHI exposure surface:** Audit confirms no PHI fields in logs, URL paths, error responses, or client-side storage. Healthcare-safe defaults enforced everywhere.

---

## 4. Constraint Architecture

Non-negotiable rules. The Architect must not deviate from these without explicit escalation and written approval.

### Technology Constraints (Hard — No Substitutions)

| Layer | Constraint |
|-------|-----------|
| Framework | Next.js 15 App Router — RSC by default, `"use client"` only when required |
| Language | TypeScript 5.x with `strict: true` — no `any`, no `@ts-ignore` |
| Styling | Tailwind CSS 4.x — utility-first only, no inline styles, no hardcoded hex colors |
| Components | shadcn/ui + Radix UI — no custom primitive equivalents |
| ORM | Prisma 6.x — `schema.prisma` is the single source of truth for the data model |
| Database | Supabase Postgres — RLS on all `teamId`-scoped tables, connection pooler for app |
| Auth | Auth.js (NextAuth) 5.x — Supabase adapter, session via `auth()` in RSC |
| Client State | Zustand 5.x — drag-and-drop state only; not a global state store |
| Server State | TanStack Query 5.x — client-side revalidation only; RSC for initial load |
| Validation | Zod 3.x — all Server Action inputs validated before any DB operation |
| Testing | Vitest + RTL (unit), Playwright (E2E) |
| Deploy | Vercel (cloud) + Docker Compose (self-host) |

### Data / Compliance Constraints (Hard)

| Rule | Rationale |
|------|-----------|
| **No PHI storage in Phase 1** | No clinical document attachments, no patient identifiers, no medical record fields. Compliance tier (Phase 3) is the right place for PHI. |
| **All tables scoped to `teamId`** | Multi-tenancy invariant. RLS enforces at DB level. Data leakage between teams is a security incident. |
| **Soft deletes only** | `deletedAt DateTime?` — no hard deletes of user data without explicit compliance flag + owner-only permission. |
| **Auth before any DB operation** | Server Actions and API routes check session/API key before touching the database. No exceptions. |

### Code Quality Constraints (Hard)

| Rule | Rationale |
|------|-----------|
| **Files ≤ 300 lines** | FRACTAL agent context management. Large files cause context drift in Feature Lead sessions. |
| **No `console.log` in committed code** | May leak PII or session data. Remove before committing. |
| **No Prisma outside `lib/db.ts`** | Connection pool exhaustion. All DB access via `import { db } from "@/lib/db"`. |

---

## 5. Failure Mode Register

Subtle ways TaskFlow fails even if it passes CI and meets technical requirements.

| # | Failure Mode | Description | Detection Signal |
|---|-------------|-------------|-----------------|
| **FM-1** | **Agent API is technically present but unusable** | REST API endpoints exist but authentication is fiddly (session-based only, no API key support), error messages are generic HTTP status codes with no body, and agent-specific patterns (source stamping, agentId attribution) are absent. FRACTAL agents can't integrate without manual workarounds. | A FRACTAL Feature Lead agent cannot complete a read-write issue cycle in a clean integration test without human intervention. |
| **FM-2** | **PHI surfaces before Phase 3** | An engineer adds a field that seems benign ("patient notes", "case reference") or logs a request body that contains identifiable clinical data. Happens gradually, not all at once. | Code review catches `PHI`, `patient`, `mrn`, `dob` field names; log audit finds identifiable strings in output. |
| **FM-3** | **Interactions feel slower than Linear** | Optimistic updates are missing on drag-and-drop or issue status changes. Mutations trigger full page reloads. RSC cache isn't invalidated correctly after Server Actions. Users feel the latency. | Manual benchmark: measure time from user action to UI update. Any interaction > 100ms perceived latency without optimistic feedback is a regression. |
| **FM-4** | **Self-host is technically possible but practically painful** | Docker Compose requires undocumented env vars, Prisma migrations fail on fresh installs, seed data is missing, or Supabase RLS policies aren't included in the setup guide. Engineers give up before first board. | Dogfood: a team member with no prior context attempts setup from scratch. > 15 minutes to first board = failure. |

> **FM-1 is the primary failure mode.** The user explicitly flagged it. Evaluate agent API ergonomics at every milestone, not just M4.

---

## 6. Autonomy Level

**Semi-autonomous**

| Decision Type | Architect Does | Escalates To User |
|--------------|---------------|-------------------|
| BLUEPRINT decomposition | Proposes workstreams + dependency graph | Yes — user approves before Feature Leads start |
| Schema changes | Proposes Prisma migration | Yes — any schema change requires user review |
| File-level implementation | Executes independently | No |
| Component structure | Decides within workstream | No |
| Test coverage approach | Decides independently | No |
| Hard blockers (build failure, ambiguous PRD) | Stops and escalates | Yes — immediately |
| New external dependencies | Proposes + waits for approval | Yes |
| API design (routes, request/response shape) | Proposes in BLUEPRINT | Yes — before Feature Lead executes |

**What this means for agents:** Do not wait for user input on implementation details inside a workstream. Do escalate immediately on schema changes, new dependencies, or anything that affects the public API surface.

---

## 7. Platform Evolution Strategy

### Current Phase: Phase 1 — Self-Serve Kanban (Composable/Headless)

**Pattern:** API-first, backend capabilities decoupled from frontend. Every mutation available via Server Action AND REST API.

**Goal:** Ship the fastest self-hosted Linear alternative with a clean REST API and team auth.

**Phase 1 Constraints:**
- ❌ No workflow automation (Phase 2)
- ❌ No analytics dashboard (Phase 3)
- ❌ No HIPAA-specific features, PHI storage, or BAA flows (Phase 3)
- ✅ Every schema decision must anticipate Phases 2–3
- ✅ REST API must be usable by FRACTAL agents from day one

### Transition to Phase 2: Agent-Native Workflows (Compound Startup)

**Trigger:** All Phase 1 milestones (M1–M4) complete and CI gate green.

**Pattern:** Cross-feature data flow IS the value. FRACTAL agents become first-class team members.

**Phase 2 additions:** FRACTAL agent API keys, workflow templates (Prior Auth Queue, CDI Worklist, Appeals Backlog, Engineering Scrum), AI issue triage, rule-based automations, inbound webhooks (GitHub, PagerDuty, EHR).

**Schema additions in Phase 2:** `AgentKey`, `Automation`, `WebhookSource`, `AuditLog` (expanded with `actorType`).

### Transition to Phase 3: Healthcare Intelligence Platform (Modular Suite)

**Trigger:** First enterprise customer with a documented HIPAA compliance requirement.

**Phase 3 additions:** HIPAA BAA tier, PHI field encryption, audit trail export, EHR webhook integrations (Epic/Cerner), clinical analytics, SSO + SCIM, platform shell.

### Phase 4+: Extension Ecosystem

**Trigger:** Active user base sufficient to attract third-party developers (not a date target).

---

## 8. Milestone Roadmap

### M1 — Core Data Model + Auth
**Scope:** Prisma schema shipped to Supabase (`Organization → Team → Board → Column → Issue → Comment`), Auth.js configured with Supabase adapter, team invite flow, RLS policies applied.

**Gates:**
- `npx prisma migrate deploy` succeeds on clean Supabase instance
- Auth E2E: user signs up → creates team → invites member → member logs in (Playwright)
- RLS verified: user from Team A cannot read Team B's issues

**Evaluator archetype:** Backend/data engineer reviewing schema integrity and multi-tenancy guarantees.

---

### M2 — Kanban Board UI
**Scope:** Drag-and-drop board with columns and issue cards (dnd-kit + LexoRank ordering), keyboard shortcuts (`c` = create, `e` = edit, `Esc` = close), column management, RSC data loading + Zustand drag state.

**Gates:**
- Playwright E2E: create board → add 3 issues → drag issue between columns → verify order persists on reload
- Lighthouse performance: no regressions on initial board load
- All interactive components push `"use client"` as deep as possible

**Evaluator archetype:** Frontend engineer who uses Linear daily — benchmarks interaction feel against Linear.

---

### M3 — Issue CRUD + Command Palette
**Scope:** Full issue lifecycle (create, edit, assign, label, set priority, set due date, close, soft delete), issue detail panel (parallel route), Cmd+K global palette (create issue, navigate board, search, change status).

**Gates:**
- All Server Actions covered by Vitest unit tests (auth check, Zod validation, success/error paths)
- Playwright E2E: full issue lifecycle from keyboard only (no mouse clicks)
- Command palette accessible from any page via `Cmd+K`

**Evaluator archetype:** Power user testing keyboard-only workflows. Every action must be reachable without a mouse.

---

### M4 — REST API + Self-Host Docs (Phase 1 Complete Gate)
**Scope:** Public REST API (`GET /api/issues`, `POST /api/issues`, `PATCH /api/issues/:id`, `POST /api/issues/:id/comments`) with API key auth, `source` + `agentId` stamping on agent mutations, Docker Compose setup, full env var reference, seed script.

**Gates:**
- All Phase 1 DoD criteria met (see Section 3)
- FRACTAL agent integration test: agent authenticates → creates issue → updates status → posts comment — no browser session
- Docker Compose: fresh `docker compose up` produces a working TaskFlow instance with seed data
- Self-host setup time dogfooded: ≤ 15 minutes from clone to first board

**Evaluator archetype:** FRACTAL Architect reviewing API ergonomics; DevOps engineer validating self-host path.

---

## 9. Source Control Preferences

| Setting | Decision |
|---------|----------|
| **Commit cadence** | Never — user commits manually. Architect and Feature Leads do not run `git commit`. |
| **PR policy** | Never auto-create. User manages all PRs manually. |
| **Worktree policy** | No worktrees by default. |

**For agents:** Do not run `git commit`, `git push`, or `gh pr create` unless explicitly instructed by the user in the current session. Produce clean, working code — let the user decide when to commit.

---

## Strategist Handoff

```
Mode:                  A — Full Discovery
Sections changed:      All (new document)
Key decisions:         Semi-autonomous Architect; user commits manually.
                       FM-1 (Agent API usability) is the primary failure mode —
                       evaluate at every milestone, not just M4.
                       No PHI in Phase 1 is a hard invariant, not a preference.
Autonomy level:        Semi-autonomous
Section 0 benchmarks:  6 capability areas scored
Phase 1 trigger:       M1–M4 all complete (feature-driven, not date-driven)
FRACTAL system doc:    .claude/fractal/FRACTALSYSTEM-taskflow.md [created]
```
