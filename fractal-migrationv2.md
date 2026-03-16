# FRACTAL Migration v2 — Distribution Review & Recommendations

**Date:** 2026-03-11
**Status:** Active
**Purpose:** Track the delta between the original application-specific FRACTAL (emtelliportal) and the current generalized distributable, then recommend changes to restore ease-of-install and prompt quality without re-introducing domain-specific branding.

---

## Table of Contents

1. [Distribution & Onboarding Principles](#1-distribution--onboarding-principles)
2. [Gap Analysis: Original vs Current](#2-gap-analysis-original-vs-current)
3. [Prioritized Recommendations](#3-prioritized-recommendations)
4. [Proof of Concept: Linear-Style Kanban Tracker (E2E Test Case)](#4-proof-of-concept-linear-style-kanban-tracker)
5. [Implementation Tracker](#5-implementation-tracker)

---

## 1. Distribution & Onboarding Principles

Derived from studying two reference repos that have high adoption and clean install flows:

- **interview-coach-skill** — a standalone Claude skill with `SKILL.md` as the single artifact. Install is `mv SKILL.md CLAUDE.md` and say `kickoff`. Two steps, under 30 seconds.
- **knowledge-work-plugins** — Anthropic's plugin marketplace. Canonical folder shape (`.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, `skills/`). Install is `claude plugin install sales@knowledge-work-plugins`. One command.

### Principle 1: Install path visible in the first screenful

The README must show the exact copy/paste steps before any conceptual explanation. Both reference repos lead with the install, not the architecture.

**Current gap:** Our README starts with a definition of FRACTAL, a mermaid diagram, and the four-tier hierarchy. The install is buried under "Quick Start" after 55 lines of conceptual content.

### Principle 2: The installable artifact must be obvious and singular

- `interview-coach-skill` ships one file (`SKILL.md`) that becomes `CLAUDE.md`.
- `knowledge-work-plugins` ships one folder per plugin with a manifest.

**Current gap:** We ship `example-claude/` alongside `agents-and-skills/`, `cursor/`, and `src/`. Three bundles that contain overlapping content. A new user has to figure out which one to use.

### Principle 3: Copy-paste must work without edits

The best onboarding requires zero customization before first use. Customization is a second step after the system is running.

**Current gap:** After copying `example-claude/`, the user must: edit `router.py` to set `BLUEPRINT_PATH`, add `.gitignore` entries, replace `{project}` in 4+ agent files, replace `{project-guides}` paths, replace `{tech-stack}` placeholders, and customize eval templates. That is framework adoption, not installation.

### Principle 4: Self-contained package shape legible at a glance

Folder names and file placement should communicate what the system does without reading docs. `commands/`, `skills/`, `agents/` are self-explanatory.

**Current gap:** Our structure is mostly good (`agents/`, `skills/`, `FRACTAL/`), but `src/` contains both reference docs and conceptual templates that overlap with `example-claude/`. The relationship between `src/ARCHITECT.md` and `example-claude/agents/architect.md` is unclear.

### Principle 5: Explicit dependencies and runtime expectations

`interview-coach-skill` requires "any paid Claude plan." `knowledge-work-plugins` lists connectors per plugin with standalone vs. supercharged comparison tables. Claude Code is the primary distribution target.

**Current gap:** Our prerequisites are scattered across three docs (`README.md`, `example-claude/README.md`, `SETUP-CLAUDE-CODE.md`). PyYAML is mentioned but easy to miss.

### Principle 6: Minimal context up front, deeper context layered later

`interview-coach-skill` asks for a resume at kickoff and layers context session-by-session. `knowledge-work-plugins` plugins work standalone and get "supercharged" with connectors.

**Current gap:** FRACTAL asks the user to customize agents, create a Strategist doc, write a BLUEPRINT, author workstream PRDs, AND configure eval templates before anything runs. There is no "zero-config first run" experience.

### Principle 7: Concrete invocation examples, not descriptions of commands

Both reference repos show exact prompts: "say `kickoff`", "type `/call-summary`". Users copy-paste into their session.

**Current gap:** Our docs describe the workflow conceptually ("the Architect decomposes the epic into workstreams") but rarely show the exact prompt a user would type to start.

### Principle 8: Local customization via overlay, not core file edits

`knowledge-work-plugins` uses `settings.local.json` and `*.local.md.example` files. Core plugin files stay untouched.

**Current gap:** We require editing core agent files to customize. There is no overlay mechanism. Upgrading FRACTAL means re-applying all customizations.

---

## 2. Gap Analysis: Original vs Current

### 2.1 Prompt Specificity

| Aspect | Original (emtelliportal) | Current (distributable) | Impact |
|--------|-------------------------|------------------------|--------|
| Architect identity | "CTO of **emtelliportal**, an Angular 21 + Tailwind CSS + Signals platform for Emtelligent's clinical NLP" | "the CTO collaborator for **{project}**. Customize this section with your project name" | Agent starts with no domain context; user must manually fill in everything |
| Tech stack | Concrete: Angular 21, Spartan UI, Tailwind, Stripe, Google Analytics | Placeholder: "[e.g. React, Angular, Vue — version and key libraries]" | Feature Leads and Architect have no stack awareness until user edits files |
| Design principles | 3 specific principles grounded in clinical mastery, provenance, and domain awareness | "Add 2–4 principles... Example: Domain awareness, Make complex feel effortless" | Principles read as generic advice rather than product-specific guardrails |
| Technical standards | Explicit forbidden patterns table (14 entries), auth patterns, token system, component conventions | "Follow the standards documented in your project's CLAUDE.md" | No actionable standards in the distributable; relies on user having a CLAUDE.md |
| Code standards in Feature Lead | Explicit: OnPush, signals, inject, files <300 lines, no PHI in URLs | "Use your project's component/framework conventions" with commented-out compliance block | Feature Lead has no constraints to enforce |

### 2.2 Strategist

| Aspect | Original | Current | Impact |
|--------|----------|---------|--------|
| Background-agent guard | Explicit check: "If spawned as background sub-agent with no active user — STOP. Write to STRATEGIST-BLOCKED.md" | Missing entirely | Strategist can be incorrectly invoked autonomously, producing inferred intent instead of interviewed intent |
| Section 0: What Right Looks Like | Full competitive benchmarking interview with 6 capability areas, example anchor products, and scored criteria | Missing entirely | The strongest specificity mechanism in the original is absent from the distributable |
| Mode selection | 4 modes (A–D) with different depth levels, ~10 to ~20 questions | No mode selection; single linear interview protocol | Less flexible for different user contexts |
| Intake pre-flight | Reads all files in `intake/` folder, summarizes what was found, tells user to add files if empty | Listed in "Context Files" section as a generic reference | No structured pre-flight protocol |
| Benchmark output | Writes `benchmarks/what-good-looks-like.md` with scored criteria per capability area | No benchmark output | No scored anchor for Layer 3/4 evaluations to reference |

### 2.3 Context Injection

| Mechanism | Original | Current | Impact |
|-----------|----------|---------|--------|
| CLAUDE.md | 650 lines of product identity, domain vocabulary, stack conventions, forbidden patterns, auth flow, design tokens, component library, design principles | Not included in distributable; user must create their own | The always-on context that grounds every session is entirely absent |
| Intake folder | Structured with token budgets, URL handling options (extract/annotate/raw), example file structure | README exists but with less guidance; no token budget rules | Users don't know how much to put in or how to format references |
| Strategist doc | Fully materialized with 329 lines of project-specific intent, 12 failure modes, specific milestone targets with numeric scores | Template only; user starts from scratch every time | No example of what a good Strategist doc looks like |
| Workstream PRDs | Tight PRDs with file paths, session protocols, acceptance criteria referencing specific routes and components | Skeleton example; placeholder structure only | Feature Leads start with almost no actionable context |

### 2.4 Distribution & Install

| Aspect | Original | Current | Impact |
|--------|----------|---------|--------|
| Install steps | Copy `.FRACTAL_AGENTS_SYSTEM` into project, run setup | Copy `example-claude/`, then edit `router.py`, add `.gitignore` entries, customize 4+ agent files, customize eval templates, create BLUEPRINT, write PRDs | 6+ manual steps before first use vs ~2 |
| Prompt bundles | One canonical source per platform | Three overlapping bundles: `example-claude/`, `agents-and-skills/`, `cursor/` | Drift risk; unclear which is canonical |
| Cursor support | N/A (Claude Code only) | Cursor folder exists but is not maintained as a first-class bundle. Cursor users should ask their LLM to reinterpret the Claude Code agents/skills into Cursor rules/skills. | Community-supported, not first-class |
| Repo name inconsistency | N/A | README uses `fractal-agents-system` in some commands, `fractal-agent-system` in others | Copy-paste fails silently |

### 2.5 Eval Templates

| Aspect | Original | Current | Impact |
|--------|----------|---------|--------|
| Deterministic eval | Real build commands: `ng build`, `npx tsc --noEmit` | Placeholder: "Replace with your build commands" | Eval gate can't run without customization |
| Strategic benchmark (Layer 4) | Specific pillars: Vault (API/auth), Workflows, Knowledge Intelligence, Ecosystem — with numeric targets per milestone | Generic template: "[Pillar 1], [Pillar 2]..." with no examples of what a real pillar looks like | The eval that answers "are we building the right thing?" has no teeth |
| Persona eval (Layer 3) | Evaluator archetypes: Technical Buyer, Clinical Ops Lead, Compliance Buyer, Demo Observer — each with domain-specific criteria | Generic structure without persona examples | Persona evals have no starting point |

---

## 3. Prioritized Recommendations

### Priority 1: Ease of Distribution & Onboarding

| # | Change | Rationale | Files Affected |
|---|--------|-----------|----------------|
| 1.1 | **Consolidate to one installable bundle (Claude Code).** Merge `agents-and-skills/` into `example-claude/`. Remove `agents-and-skills/` as a separate directory. `example-claude/` becomes the canonical bundle. Keep `cursor/` as-is with a short `cursor/README.md` directing Cursor users to ask their LLM to reinterpret the Claude Code agents/skills. | Eliminates the "which folder do I use?" confusion. Cursor is community-supported, not first-class. | `agents-and-skills/`, `example-claude/`, `cursor/README.md`, `README.md` |
| 1.2 | **Move install steps to the top of README.md** — before the architecture explanation. Lead with `cp -r` and `mv` commands. | Follows Principle 1: install path visible in first screenful. | `README.md` |
| 1.3 | **Ship a sample `CLAUDE.md` template** inside `example-claude/` with concrete sections (product identity, stack, commands, conventions, forbidden patterns) pre-filled for a realistic demo project. | Currently the most impactful missing piece. The always-on context doc grounds every session. Shipping one with concrete (but de-identified) content gives users a starting point rather than a blank page. | New: `example-claude/CLAUDE.md` |
| 1.4 | **Fix the repo name inconsistency** in all copy-paste commands. Standardize on `fractal-agent-system` everywhere. | Broken copy-paste commands kill onboarding. | `README.md` |
| 1.5 | **Add a "First Run" section** showing exact prompts the user would type after install: e.g., "Open Claude Code. Type: `Use the strategist agent to interview me and generate STRATEGIST-myapp.md`" | Users need to see the exact invocation, not a description of the workflow. | `README.md`, `example-claude/README.md` |

### Priority 2: Prompt Parity (De-identified Specificity)

| # | Change | Rationale | Files Affected |
|---|--------|-----------|----------------|
| 2.1 | **Restore Section 0 (What Right Looks Like) to the Strategist.** Port the competitive benchmarking interview from the original, with generic capability areas (Developer UX, API Management, Core Workflow, Data Processing, Notifications, Billing) instead of healthcare-specific ones. | This is the highest-value specificity mechanism. Scored benchmarks anchor all Layer 3/4 evaluations. Without it, "good" is subjective. | `example-claude/agents/strategist.md` |
| 2.2 | **Restore the background-agent guard to the Strategist.** Add the check for autonomous invocation and the `STRATEGIST-BLOCKED.md` fallback. | Prevents the most common misuse: spawning Strategist as a background agent that infers intent from code instead of interviewing the user. | `example-claude/agents/strategist.md` |
| 2.3 | **Restore mode selection (A–D) to the Strategist.** Port the four intake modes with their question counts. | Different projects need different depths. The linear-only protocol forces a one-size-fits-all interview. | `example-claude/agents/strategist.md` |
| 2.4 | **Fill the Architect with concrete defaults** instead of placeholders. Replace `{project}` preamble with a filled-in demo identity. Add a "Customize" callout block explaining what to change, rather than leaving the whole file as a template. | An Architect that starts with "I am the CTO of TaskFlow, a Next.js 15 + TypeScript + Prisma kanban application" is immediately useful even before customization. `{project}` placeholders are not. | `example-claude/agents/architect.md` |
| 2.5 | **Fill the Feature Lead with concrete code standards** instead of "follow your CLAUDE.md." Ship 5–8 real standards (typed APIs, files <300 lines, no hardcoded secrets, tests for new code, lint must pass). | Feature Leads need constraints from line 1. "See your CLAUDE.md" is a dead reference for new adopters who haven't written one yet. | `example-claude/agents/feature-lead.md` |
| 2.6 | **Ship a materialized example Strategist doc** (`STRATEGIST-example.md`) alongside the agent. Show what a completed interview output looks like for a realistic project. | Users need to see a good Strategist doc before they can produce one. Currently no example exists. | New: `example-claude/FRACTAL/STRATEGIST-example.md` |
| 2.7 | **Fill eval templates with realistic examples.** Deterministic eval: include sample build/lint/typecheck commands for 3 common stacks. Strategic benchmark: include 3–4 example pillars with scoring criteria. Persona eval: include 2–3 example evaluator archetypes. | Templates with `[Pillar 1]` placeholders don't teach the user what good evals look like. | `example-claude/FRACTAL/EVAL_TEMPLATES/*.md` |

### Priority 3: Maintainability & Runtime

| # | Change | Rationale | Files Affected |
|---|--------|-----------|----------------|
| 3.1 | **Remove `agents-and-skills/` directory** after merging into `example-claude/`. | Eliminates the duplicate prompt bundle and the associated drift risk. | `agents-and-skills/` (delete) |
| 3.2 | **Move `src/` conceptual docs into a `docs/` folder** and clearly label them as reference/theory, not installable artifacts. | `src/` currently confuses "reference docs about FRACTAL" with "things you install." Renaming to `docs/` makes the distinction clear. | `src/` -> `docs/` |
| 3.3 | **Add router CLI argument for BLUEPRINT path** instead of requiring a constant edit. Support `python3 router.py --blueprint BLUEPRINT-MyEpic.yaml init` alongside the current constant. | Reduces friction when switching epics and eliminates a manual file edit. | `ROUTING_LOGIC/router.py` |
| 3.4 | **Add an overlay/local-config mechanism** for agent customization. Support `architect.local.md` that gets merged with the base `architect.md`, so upgrades don't require re-applying customizations. | Follows Principle 8 from reference repos. Separates core FRACTAL from project-specific customization. | Agent loading logic, documentation |
| 3.5 | **Consolidate setup docs.** Merge `SETUP-CLAUDE-CODE.md` into `example-claude/README.md`. Remove the separate setup file. `SETUP-CURSOR.md` can be archived or replaced with a pointer to `cursor/README.md`. | Onboarding should be in one place, not spread across 3–4 docs. | `SETUP-CLAUDE-CODE.md`, `example-claude/README.md` |
| 3.6 | **Add intake folder token budget guidance** to the distributable `intake/README.md`, ported from the original. | The original's token-budget rules and URL handling options are genuinely useful and currently missing. | `example-claude/FRACTAL/intake/README.md` |

---

## 4. Proof of Concept: Linear-Style Kanban Tracker

This test case validates the full FRACTAL system E2E using a bounded, realistic product brief. The intent is to prove that an adopter can install FRACTAL, run the Strategist interview, produce a BLUEPRINT, execute workstreams, and complete the eval loop — all using the distributable repo without modifications beyond the documented customization steps.

### 4.1 Product Brief

**Product:** TaskFlow — a Linear-style kanban project tracker
**Stack:** Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Prisma + Supabase Postgres + Auth.js
**Scope:** MVP with board view, issue CRUD, drag-and-drop reordering, team filtering, and keyboard shortcuts
**Timeline:** Proof-of-concept in one FRACTAL epic (~6 workstreams)

### 4.2 Benchmark Anchors (Section 0: What Right Looks Like)

| Capability Area | Benchmark Product | What They Do Right |
|----------------|-------------------|-------------------|
| Board UX | Linear | Keyboard-first navigation; issues feel instant; no page reloads on state change |
| Issue detail | Linear | Side panel, not a full page. Context preserved. Markdown editor with slash commands |
| Filtering & views | Notion | Flexible compound filters; saved views; toggle between board/list/table |
| Real-time sync | Figma | Cursor presence, live updates without refresh, conflict-free |
| Keyboard shortcuts | Linear | Global command palette (Cmd+K); single-key shortcuts for common actions (C=create, X=select) |
| Onboarding | Vercel | Zero-config first project; useful default content; progressive feature disclosure |

### 4.3 Sample Strategist Doc Outline

```markdown
## 1. Project Mandate
Build a fast, keyboard-driven kanban tracker that matches Linear's interaction quality
for small teams (2-10 people), shipping as a self-hosted OSS tool.

## 2. Core Intent & Guiding Principles
1. Speed is the feature — every interaction < 100ms perceived latency
2. Keyboard-first, mouse-optional — power users never touch the mouse
3. Opinionated defaults over configuration — one board layout, one workflow
4. Local-first optimistic updates — UI never waits for the server

## 3. Definition of Done
- [ ] Board renders 100 issues without jank (60fps drag, <50ms filter)
- [ ] Full CRUD: create, edit, status change, archive, delete
- [ ] Drag-and-drop reordering persists across sessions
- [ ] Cmd+K command palette with 10+ actions
- [ ] Team member filtering with avatar chips
- [ ] Dark mode + light mode
- [ ] Auth flow: signup -> first board -> first issue in < 2 minutes

## 4. Constraint Architecture
- Next.js 15 with App Router and Server Components for initial load
- Prisma ORM as single source of truth for data models (schema-driven development)
- Supabase Postgres with RLS on all team-scoped tables
- Auth.js (NextAuth) with Supabase adapter for authentication
- Tailwind CSS + shadcn/ui for UI components (no custom component library)
- Bundle < 200KB gzipped

## 5. Failure Mode Register
- "Feels sluggish" — optimistic updates are critical; any server-wait kills trust
- "Too many clicks" — every action should be reachable in <= 2 interactions
- "Looks like a Trello clone" — visual identity must be closer to Linear than Trello
- "Can't find my issues" — filtering and search must work on 500+ issues

## 6. Autonomy Level
Semi-autonomous — Architect can make implementation decisions but must surface
any UX-impacting architectural choice for review.

## 7–8. Milestones
M1: Board renders with mock data + drag-and-drop (validates core interaction model)
M2: Supabase backend + real CRUD + auth (validates data layer)
M3: Keyboard shortcuts + command palette + filtering (validates power-user experience)

## 9. Source Control
Per-phase commits. PR at epic completion. No worktrees.
```

### 4.4 Expected BLUEPRINT Structure

```yaml
- name: FeatureLead-BoardShell
  model: sonnet
  dependencies: []
  prd: workstreams/board-shell.md
  description: Board layout component with column rendering and responsive grid

- name: FeatureLead-IssueCRUD
  model: sonnet
  dependencies: []
  prd: workstreams/issue-crud.md
  description: Issue create/edit/archive/delete with optimistic updates

- name: FeatureLead-DragAndDrop
  model: sonnet
  dependencies: [FeatureLead-BoardShell]
  prd: workstreams/drag-and-drop.md
  description: Drag-and-drop reordering with persistence and animation

- name: FeatureLead-AuthAndData
  model: sonnet
  dependencies: []
  prd: workstreams/auth-and-data.md
  description: Prisma schema, Supabase Postgres migrations, RLS policies, Auth.js setup

- name: FeatureLead-KeyboardNav
  model: sonnet
  dependencies: [FeatureLead-BoardShell, FeatureLead-IssueCRUD]
  prd: workstreams/keyboard-nav.md
  description: Command palette, single-key shortcuts, focus management

- name: FeatureLead-FilteringAndViews
  model: sonnet
  dependencies: [FeatureLead-IssueCRUD, FeatureLead-AuthAndData]
  prd: workstreams/filtering-and-views.md
  description: Compound filters, team member chips, saved filter views
```

### 4.5 Sample Workstream PRD: board-shell.md

```markdown
# Workstream: Board Shell

## Goal
Render a kanban board with configurable columns (Backlog, Todo, In Progress, Done)
and a responsive grid layout that adapts from 1-column mobile to 4-column desktop.

## Acceptance Criteria
- [ ] Board renders 4 columns with correct headers
- [ ] Columns accept issue card children (placeholder cards for now)
- [ ] Layout is responsive: 1-col on mobile, 2-col on tablet, 4-col on desktop
- [ ] Column widths are equal and scrollable when cards overflow
- [ ] Empty state shows "No issues" message per column
- [ ] Dark mode and light mode both render correctly

## File Manifest

**Read:**
- `app/layout.tsx` (root layout pattern)
- `app/globals.css` (design tokens, Tailwind config)
- `components/ui/` (shadcn/ui primitives already installed)
- `CLAUDE.md` (component conventions, forbidden patterns)

**Write:**
- `components/board/Board.tsx`
- `components/board/Column.tsx`
- `components/board/ColumnHeader.tsx`
- `components/board/EmptyState.tsx`

## Session Protocol
1. Read all files in the read manifest before writing anything
2. Use shadcn/ui primitives and Tailwind utility classes — no custom CSS unless Tailwind cannot express it
3. All components must be typed (no `any`)
4. Verify: `npm run build` (Next.js build) passes with no errors
5. Verify: `npx tsc --noEmit` passes with no type errors

## Context
This is the foundation workstream. DragAndDrop and KeyboardNav depend on the board
layout structure. Column IDs must be stable identifiers (not array indices) because
drag-and-drop reordering and keyboard navigation both reference them.

## Guide References
- `CLAUDE.md` — component patterns, forbidden patterns
```

### 4.6 Success Criteria for E2E Validation

The FRACTAL system passes the E2E test if all of the following are true:

| Step | Validates | Pass Criteria |
|------|-----------|---------------|
| Install | Distribution (Principle 1–3) | `cp -r example-claude .claude` works. No edits required before first invocation. |
| Strategist interview | Strategist agent + intake flow | Agent conducts interactive interview, produces `STRATEGIST-taskflow.md` with all 9 sections + Section 0 benchmarks. Agent blocks if invoked as background agent. |
| BLUEPRINT creation | Architect agent + BLUEPRINT authoring | Architect reads Strategist doc, produces valid `BLUEPRINT-TaskFlow.yaml` with 6 workstreams and correct dependency edges. `router.py init` succeeds. |
| Workstream execution | Feature Lead + router | `router.py next` returns `FeatureLead-BoardShell` and `FeatureLead-IssueCRUD` (parallel, no dependencies). Feature Lead reads PRD, implements, emits PULSE, writes HANDOFF.md. |
| Eval gate | Deterministic + LLM judgment evals | Layer 1 runs real build commands. Layer 2 evaluates intent alignment. HANDOFF accepted or rejected with specific feedback. |
| Epic completion | Router status + commit flow | `router.py status` shows 6/6 COMPLETE. Architect invokes commit-summarize. |
| Gap analysis | Milestone evaluation | `/gap-analysis` runs at M1 boundary, produces prioritized gap list (P0/P1/P2). |

### 4.7 What This Test Case Proves

1. **Install works without domain expertise.** A kanban tracker has no healthcare, finance, or compliance prerequisites. Anyone can validate.
2. **The Strategist interview produces actionable output.** Section 0 benchmarks, failure modes, and milestone gates are concrete, not generic.
3. **BLUEPRINTs decompose correctly.** Dependency edges match real implementation constraints (drag-and-drop depends on board-shell).
4. **Feature Leads execute from cold context.** Each PRD is self-contained with file manifests, acceptance criteria, and session protocols.
5. **The eval loop catches real issues.** Deterministic eval gates against actual build output, not self-reported status.
6. **The router orchestrates correctly.** Parallel workstreams start together; dependent workstreams wait.

---

## 5. Implementation Tracker

**Overall Progress: 18/18 (100%)**

| # | Recommendation | Status | Notes |
|---|---------------|--------|-------|
| 1.1 | Consolidate to one bundle (Claude Code) | ✅ Complete | `agents-and-skills/` removed; `example-claude/` is canonical; `cursor/README.md` added with reinterpret note |
| 1.2 | Move install to top of README | ✅ Complete | Install is first section after title; before architecture explanation |
| 1.3 | Ship sample CLAUDE.md template | ✅ Complete | `example-claude/CLAUDE.md` — TaskFlow kanban demo project with full sections |
| 1.4 | Fix repo name inconsistency | ✅ Complete | All `fractal-agents-system` → `fractal-agent-system` in SETUP-CURSOR.md and README.md |
| 1.5 | Add "First Run" prompts | ✅ Complete | Exact copy-paste prompts in README.md and `example-claude/README.md` |
| 2.1 | Restore Section 0 to Strategist | ✅ Complete | Full competitive benchmarking interview with 6 generic capability areas and scoring |
| 2.2 | Restore background-agent guard | ✅ Complete | Guard at top of Strategist with STRATEGIST-BLOCKED.md fallback |
| 2.3 | Restore mode selection (A–D) | ✅ Complete | 4 modes: Full Discovery (~20q), Focused (~12q), Express (~6q), Refresh (~3q) |
| 2.4 | Fill Architect with concrete defaults | ✅ Complete | TaskFlow identity (Next.js 15 + Prisma + shadcn/ui), concrete principles and standards |
| 2.5 | Fill Feature Lead with concrete standards | ✅ Complete | 8 Always standards + 6 Never standards; stack-agnostic |
| 2.6 | Ship example Strategist doc | ✅ Complete | `STRATEGIST-example.md` — full TaskFlow doc with all 10 sections including Section 0 benchmarks |
| 2.7 | Fill eval templates with examples | ✅ Complete | Deterministic: 3-stack command tables. Strategic: 4 example pillars with scoring. Persona: 3 archetypes with questions. LLM judgment: example principles. |
| 3.1 | Remove `agents-and-skills/` | ✅ Complete | Directory removed via `git rm -rf` |
| 3.2 | Rename `src/` to `docs/` | ✅ Complete | `git mv src docs`; updated SETUP-CURSOR.md reference |
| 3.3 | Add router CLI argument for BLUEPRINT | ✅ Complete | `--blueprint` flag on `router.py` overrides constant; backward compatible |
| 3.4 | Add overlay/local-config mechanism | ✅ Complete | `*.local.md` overlay documented in README.md and `example-claude/README.md` |
| 3.5 | Consolidate setup docs (Claude Code only) | ✅ Complete | `example-claude/README.md` is now self-contained with install, first run, customize, and workflow sections |
| 3.6 | Add intake token budget guidance | ✅ Complete | Already present in `example-claude/FRACTAL/intake/README.md` (verified) |
