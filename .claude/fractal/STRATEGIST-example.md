# STRATEGIST — TaskFlow

> **This is a sample Strategist document** for the TaskFlow demo project (a Linear-style kanban tracker).
> It demonstrates what a completed Strategist interview output looks like. Use it as a reference when generating your own.

**Generated:** 2026-03-11
**Mode:** A — Full Discovery
**Interviewer:** Strategist Agent (Tier 0)

---

## 0. What Right Looks Like

| Capability Area | Benchmark Product | What They Do Right | Target (1–5) |
|----------------|-------------------|-------------------|--------------|
| Board UX | Linear | Keyboard-first navigation; issues feel instant; no page reloads on state change; drag-and-drop is 60fps | 5/5 |
| Issue Detail | Linear | Side panel (not a full page), context preserved, Markdown editor with slash commands | 4/5 |
| Filtering & Views | Notion | Flexible compound filters, saved views, toggle between board/list/table | 3/5 |
| Real-time Sync | Figma | Cursor presence, live updates without refresh, conflict-free merging | 2/5 |
| Keyboard Shortcuts | Linear | Global command palette (Cmd+K), single-key shortcuts for common actions (C=create, X=select, S=status) | 5/5 |
| Onboarding | Vercel | Zero-config first project, useful default content, progressive feature disclosure | 4/5 |

**Key takeaway:** Board UX and keyboard shortcuts are non-negotiable at launch (5/5). Real-time sync is a phase 2 feature (2/5) — don't over-invest in it for MVP.

---

## 1. Project Mandate

Build a fast, keyboard-driven kanban tracker that matches Linear's interaction quality for small teams (2–10 people), shipping as a self-hosted open-source tool.

---

## 2. Core Intent & Guiding Principles

In priority order:

1. **Speed is the feature** — Every interaction under 100ms perceived latency. Optimistic updates everywhere. If the user can perceive a loading spinner, something is wrong.
2. **Keyboard-first, mouse-optional** — Power users never touch the mouse. Single-key shortcuts for all common actions. Command palette as the universal entry point.
3. **Opinionated defaults over configuration** — One board layout, one workflow (Backlog → Todo → In Progress → Done). Reduce decision fatigue. Add flexibility later, not now.
4. **Local-first optimistic updates** — The UI never waits for the server. Mutations apply instantly and reconcile asynchronously. Conflicts are rare at our scale; handle them simply (last-write-wins).

---

## 3. Definition of Done

- [ ] Board renders 100 issues without jank (60fps drag, <50ms filter response)
- [ ] Full CRUD: create, edit, status change, archive, delete — all with optimistic updates
- [ ] Drag-and-drop reordering persists across sessions (database-backed sort order)
- [ ] Cmd+K command palette with 10+ actions (create, search, navigate, change status)
- [ ] Single-key shortcuts: C (create), X (select), S (status menu), / (search), Esc (dismiss)
- [ ] Team member filtering with avatar chips (click to filter, click again to remove)
- [ ] Dark mode + light mode (system preference default, manual toggle)
- [ ] Auth flow: signup → first board → first issue in under 2 minutes
- [ ] Bundle size < 200KB gzipped (initial load)
- [ ] Lighthouse performance score > 90 on board page

---

## 4. Constraint Architecture

- **Framework:** Next.js 15 with App Router and Server Components for initial load
- **ORM:** Prisma as single source of truth for data models (schema-driven development)
- **Database:** Supabase Postgres with RLS on all team-scoped tables
- **Auth:** Auth.js (NextAuth) with Supabase adapter
- **UI:** Tailwind CSS + shadcn/ui for all components (no custom component library)
- **Bundle budget:** < 200KB gzipped initial load
- **No paid dependencies:** All core dependencies must be open-source
- **Single-region deploy:** Vercel + Supabase in a single region (latency acceptable at 2–10 user scale)

---

## 5. Failure Mode Register

| # | Failure Mode | Why It's Subtle | Mitigation |
|---|-------------|----------------|------------|
| 1 | "Feels sluggish" | Optimistic updates are critical; any visible server-wait destroys the speed perception that is our primary differentiator | Every mutation must use `useOptimistic`. Measure P95 interaction latency. Budget: < 100ms. |
| 2 | "Too many clicks" | Death by a thousand cuts — each extra click seems minor but compounds into "this tool slows me down" | Every action reachable in ≤ 2 interactions. Keyboard shortcuts for top-10 actions. |
| 3 | "Looks like a Trello clone" | Visual identity must be closer to Linear than Trello. If users say "it's just another Trello," we've failed positioning. | Visual density, monospace data, compact cards. No rounded-corner card stacks. |
| 4 | "Can't find my issues" | At 500+ issues, search and filtering become critical. If filtering is slow or imprecise, power users abandon the tool. | Compound filters, full-text search, saved views. Test with 1000-issue dataset. |
| 5 | "Onboarding takes too long" | If signup → useful board takes more than 2 minutes, we lose first-time users before they see value | Seed first board with example issues. Skip optional setup steps. Tutorial via progressive disclosure, not modal wizards. |
| 6 | "Not sure if my changes saved" | Optimistic updates without confirmation create anxiety: "did that actually work?" | Subtle success indicators (brief color flash on saved card, toast for destructive actions only). |

---

## 6. Autonomy Level

**Semi-autonomous** — The Architect can make implementation decisions (file structure, component boundaries, API shape) without asking. But the Architect must surface any **UX-impacting architectural choice** for review before proceeding. Examples that require review:

- Changing the board layout model (columns, swimlanes)
- Choosing between server-side vs. client-side rendering for a user-facing page
- Adding a new dependency that affects bundle size
- Changing the auth flow or adding new auth providers

---

## 7. Platform Evolution Strategy

**Current phase:** MVP — single-team kanban with core CRUD and keyboard navigation.

**Next phase:** Multi-team support, real-time collaboration, and API/webhooks for integrations.

**Phase transition criteria:**
- MVP ships and 5+ teams use it weekly for 2+ weeks
- No P0 bugs in the core board/issue workflow
- Performance benchmarks met (60fps drag, <50ms filter, <200KB bundle)

**Architecture for current phase:**
- Single-tenant schema with `teamId` on every table (prepares for multi-team without over-engineering)
- No real-time infrastructure yet — SWR polling is sufficient at 2–10 user scale
- No API versioning — internal APIs only until public API phase

---

## 8. Milestone Roadmap

### M1: Board + Drag-and-Drop (validates core interaction model)
- Board renders with 4 columns and placeholder cards
- Drag-and-drop reordering with 60fps animation
- Dark mode + light mode
- **Gap analysis trigger:** Does the board feel fast? Does drag-and-drop feel native?
- **Evaluator archetypes:** End User (speed, tactile feedback), Demo Observer (visual polish)

### M2: Data Layer + Auth (validates backend)
- Prisma schema with Issue, Board, Column, User, Team models
- Supabase Postgres with RLS policies
- Auth.js signup/login flow
- Full CRUD with optimistic updates
- **Gap analysis trigger:** Is the auth flow < 2 minutes? Do optimistic updates feel instant?
- **Evaluator archetypes:** Technical Buyer (auth, security, data model), End User (CRUD speed)

### M3: Keyboard Navigation + Filtering (validates power-user experience)
- Cmd+K command palette with 10+ actions
- Single-key shortcuts for all common actions
- Compound filters with team member chips
- Saved filter views
- **Gap analysis trigger:** Can a power user complete a full workflow without touching the mouse?
- **Evaluator archetypes:** Power User (keyboard efficiency, discoverability), Demo Observer (wow factor)

---

## 9. Source Control Preferences

- **Commit cadence:** Per-phase — commit after all workstreams in a BLUEPRINT phase are COMPLETE
- **PR policy:** Auto-create PR at epic completion
- **Worktree policy:** No worktrees — single branch per epic
