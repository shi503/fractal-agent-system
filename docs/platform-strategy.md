# TaskFlow Platform Blueprint
## Architecture & Evolution Strategy — AI Agent Reference Document

**Version:** 1.0
**Status:** Strategic Reference — Platform vision and phase roadmap. For coding implementation, defer to `CLAUDE.md` and `docs/frontend-dev-guide.md` which take precedence on all TypeScript/CSS/Next.js decisions.
**Audience:** Engineering contributors, product stakeholders, AI agents making architectural (not implementation) decisions

---

## 1. Purpose of This Document

This document is the **strategic reference** for architectural decisions on TaskFlow. It answers three questions:

1. **What are we building?** — A HIPAA-aware, FRACTAL agent-native kanban board for healthcare teams, not a generic todo app.
2. **Why this architecture?** — First-principles reasoning from best-in-class SaaS patterns applied to the healthcare market.
3. **How does it evolve?** — A phased roadmap from self-serve kanban to healthcare intelligence platform.

**Decision Rule for AI Agents:**
For platform-level architectural decisions (schema design, phase scope, data model evolution), this document provides strategic context. For TypeScript and Next.js implementation decisions, `CLAUDE.md` and `frontend-dev-guide.md` take precedence and must be followed exactly. If a proposed schema or API change conflicts with the principles here, flag it for human review before proceeding.

---

## 2. Strategic Identity

### What We Are

| Dimension | We ARE | We ARE NOT |
|-----------|--------|------------|
| **Category** | Healthcare-aware project management SaaS | Generic task management tool |
| **Analog** | "Linear for healthcare teams" | Jira (heavyweight) / Trello (too simple) |
| **Moat** | HIPAA compliance + FRACTAL agent-native task creation | Manual keyboard-only task management |
| **Buyer** | Engineering leads at healthtech companies; clinical ops managers | Individual consumers |
| **Competes with** | Linear, Jira, Asana, GitHub Projects | Notion, Monday.com, Todoist |

### Core Differentiators (Non-Negotiable in All Architecture Decisions)

1. **FRACTAL Agent Integration:** AI agents create, triage, update, and close issues natively. Not a webhook afterthought — agents are first-class participants in the board.
2. **Healthcare Compliance Tier:** HIPAA BAA, audit trails, data residency controls available as an opt-in tier. Not bolted on later.
3. **Keyboard-first UX:** Every action reachable from keyboard (Cmd+K palette, `c` to create, `e` to edit). Speed matches Linear.
4. **Self-hostable:** Open-source core. Healthcare orgs can deploy behind their own firewall with full data ownership.

---

## 3. Architecture Patterns — What Good Looks Like

We studied best-in-class SaaS platforms to select our architectural approach.

### Pattern Assessment Matrix

| Pattern | Description | Exemplars | Fit | Rationale |
|---------|-------------|-----------|-----|-----------|
| **Unified Monolith** | Single codebase, all features tightly coupled | Basecamp, early Asana | ❌ Reject | Doesn't support incremental adoption. Hard to open-source selectively. |
| **Modular Suite** | Separate products, shared platform layer (identity, data, design system) | Atlassian, Google Workspace | ✅ Target state (Phase 3) | Balances team autonomy with unified UX. Enables healthcare-specific modules alongside core kanban. |
| **Platform + Marketplace** | Core platform + third-party extensions | Jira Apps, Monday apps | ⏳ Future (Phase 4+) | Requires active user base to attract developers. Plan extension points, don't build the marketplace yet. |
| **Integration Hub** | Connective tissue between external systems | Zapier, Make | 🔄 Partial | We should offer integrations (GitHub, Slack, EHR webhooks) without becoming an iPaaS ourselves. |
| **Composable / Headless** | API-first, backend capabilities decoupled from frontend | Linear API, Notion API | ✅ Starting point (Phase 1) | Correct launch architecture. REST API + portal. Enables FRACTAL agent access from day one. |
| **Compound Startup** | Multiple tightly integrated products where integration IS the value | Rippling, Linear | ✅ Phase 2 evolution | Once we have workflow templates + AI triage + compliance reporting, cross-feature data flow is the differentiator. |

### Our Chosen Path

```
Phase 1: Self-Serve Kanban (Composable/Headless)
    ↓
Phase 2: Agent-Native Workflows (Compound — FRACTAL + clinical workflow templates)
    ↓
Phase 3: Healthcare Intelligence Platform (Modular Suite — compliance tier, analytics, EHR)
    ↓
Phase 4+: Extension Ecosystem (Platform + Marketplace)
```

---

## 4. Architecture — Phase Definitions

### Phase 1: Self-Serve Kanban

**Pattern:** Composable/Headless
**Goal:** Ship a production-quality self-hosted kanban board that healthcare engineering teams choose over Linear for its HIPAA awareness and FRACTAL integration.

```
┌─────────────────────────────────────────────┐
│              TaskFlow Frontend               │
│         (Next.js + Tailwind + shadcn/ui)    │
│                                              │
│  ┌──────────┬──────────┬──────────────────┐  │
│  │  Boards  │  Issues  │  Command Palette  │  │
│  │ (kanban) │  detail  │  (Cmd+K)          │  │
│  └──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────┤
│         Server Actions + REST API            │
│    (auth-first, Zod-validated, typed)        │
├─────────────────────────────────────────────┤
│         PostgreSQL (Supabase)                │
│  ┌────────────────────────────────────────┐  │
│  │ Org → Team → Board → Column →          │  │
│  │   Issue → Comment                      │  │
│  └────────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│         Auth.js v5 (Supabase adapter)        │
└─────────────────────────────────────────────┘
```

**Phase 1 Deliverables:**

| Deliverable | Priority | Description |
|-------------|----------|-------------|
| **Core Data Model** | P0 | `Organization → Team → Board → Column → Issue → Comment` in Supabase. All future features build on this. |
| **Kanban Board UI** | P0 | Drag-and-drop columns and issues (dnd-kit). Column ordering. Issue reordering within/across columns. |
| **Issue CRUD** | P0 | Create, view, edit, delete issues. Assignee, label, priority, due date fields. Keyboard shortcuts. |
| **Command Palette** | P0 | Cmd+K global palette: create issue, navigate to board, search issues, change status. |
| **Team Auth** | P0 | Invite team members via email. Role-based: Owner, Member, Viewer. |
| **REST API** | P1 | Public API for FRACTAL agents: `GET /issues`, `POST /issues`, `PATCH /issues/:id`, `POST /issues/:id/comments`. |
| **Self-Host Docs** | P1 | Docker Compose setup. Environment variable reference. Supabase local dev setup. |

**Phase 1 Schema Principles:**

| Principle | Implementation |
|-----------|---------------|
| **Multi-tenant from day one** | All tables scoped to `teamId`. RLS in Supabase enforces at DB level. |
| **Agent-accessible** | `Issue` table has `source` field (`human` \| `agent`) + `agentId` for attribution. |
| **Audit trail built-in** | `createdAt`, `updatedAt`, `createdById` on every table. Soft deletes (`deletedAt`). |
| **Ordered collections** | `Column.order` and `Issue.order` use float ordering (LexoRank-style) for efficient reorder without full table update. |

**Phase 1 Constraints (AI Agent Rules):**
- ❌ Do NOT build workflow automation (that's Phase 2)
- ❌ Do NOT build a reporting dashboard (that's Phase 3)
- ❌ Do NOT build HIPAA-specific features (PHI storage, BAA flows) — compliance tier is Phase 3
- ✅ DO make every schema decision with Phases 2-3 in mind
- ✅ DO ensure the REST API is usable by FRACTAL agents without a browser session
- ✅ DO use feature flags for any experimental UI features

---

### Phase 2: Agent-Native Workflows

**Pattern:** Compound Startup
**Goal:** FRACTAL agents become first-class team members. Clinical workflow templates let healthcare ops teams manage prior auth queues, CDI worklists, and appeals backlogs inside TaskFlow.

**Phase 2 Key Additions:**

| Addition | Purpose | Precedent |
|----------|---------|-----------|
| **FRACTAL Agent API Keys** | Agents authenticate with scoped API keys. `agentId` stamped on all mutations. Activity visible in issue timeline. | Linear API, GitHub Apps |
| **Workflow Templates** | Pre-built board templates: Engineering Scrum, Prior Auth Queue, CDI Worklist, Appeals Backlog. One-click setup. | Notion templates, Linear workflows |
| **AI Issue Triage** | Inbound issues (from webhooks/agents) auto-labeled, prioritized, and assigned based on content. | Linear's AI triage (2024) |
| **Automations** | Rule-based triggers: "When issue moves to Done → notify Slack", "When priority = P0 → assign to on-call". | Linear automations, Jira rules |
| **Webhook Inbound** | External systems push events → TaskFlow creates/updates issues. GitHub PRs, PagerDuty alerts, EHR status changes. | Linear webhooks |

**Phase 2 Schema Evolution:**

| Entity | Phase 1 | Phase 2 Addition |
|--------|---------|-----------------|
| `Organization` | ✅ | Add: `tier` (free \| pro \| healthcare), feature flags |
| `Team` | ✅ | Add: `workflowType` enum (engineering \| clinical_ops \| mixed) |
| `Issue` | ✅ | Add: `source` (human \| agent \| webhook), `externalId`, `automationState` |
| `AgentKey` | ❌ | NEW: API keys scoped per agent, per team, with permission set |
| `Automation` | ❌ | NEW: trigger conditions + action rules, linked to board |
| `WebhookSource` | ❌ | NEW: inbound webhook config (GitHub, PagerDuty, custom) |
| `AuditLog` | Basic | Expanded: all mutations logged with actor type (human \| agent \| automation), IP |

**Clinical Workflow Templates — Phase 2 Examples:**

| Template | Columns | Use Case |
|----------|---------|----------|
| **Prior Auth Queue** | Received → In Review → Peer Review → Approved / Denied | UM nurses tracking PA requests |
| **CDI Worklist** | Assigned → In Progress → Queried → Resolved | Clinical documentation improvement |
| **Appeals Backlog** | Filed → Evidence Gathering → Submitted → Decision | RCM teams managing denial appeals |
| **Engineering Scrum** | Backlog → In Progress → In Review → Done | Engineering teams, 2-week sprints |

> **Template note:** These are pre-configured board layouts, NOT custom business logic. The underlying data model is the same `Column → Issue` structure for all templates. Domain-specific behavior lives in labels, custom fields, and automation rules — not in separate code paths.

**Phase 2 Constraints (AI Agent Rules):**
- ❌ Do NOT build HIPAA PHI storage features yet (no clinical document attachment with PHI)
- ❌ Do NOT allow agent API keys with admin permissions (agents can create/update/close issues; they cannot delete boards or manage team membership)
- ✅ DO stamp `source: "agent"` and `agentId` on all agent-created mutations
- ✅ DO log all automation triggers in `AuditLog` with input, rule matched, and action taken
- ✅ DO version automation rules (don't mutate existing rules — create new versions)

---

### Phase 3: Healthcare Intelligence Platform

**Pattern:** Modular Suite with Compliance Tier
**Goal:** Full HIPAA BAA tier, clinical audit trails, EHR webhook integrations, analytics dashboards. The platform healthcare organizations trust for regulated workflows.

**Phase 3 Key Additions:**

| Addition | Purpose | Precedent |
|----------|---------|-----------|
| **HIPAA Compliance Tier** | BAA signing flow, PHI field encryption, data residency controls, audit export | Notion Enterprise, Linear Enterprise |
| **Audit Trail Export** | Full activity export for compliance reviews: who changed what, when, why | Epic audit logging, SOC2 evidence collection |
| **EHR Webhook Integration** | Epic/Cerner status changes trigger TaskFlow issue updates (e.g., PA decision → close issue) | Redox, Health Gorilla webhooks |
| **Clinical Analytics** | Dashboard: PA approval rates, average time-to-resolution by workflow type, agent vs. human throughput | Looker, Amplitude |
| **Platform Shell** | Unified nav across modules, cross-team search, notification center | Atlassian unified nav |
| **SSO + SCIM** | Enterprise identity (Okta, Azure AD), automated user provisioning/deprovisioning | Standard enterprise SaaS |

---

## 5. Shared Infrastructure — Cross-Phase Requirements

These infrastructure layers are built incrementally but must be **planned from Phase 1**.

### 5.1 Entity Graph

| Phase | Entities | Relationships |
|-------|----------|---------------|
| **1** | Organization, User, Team, Board, Column, Issue, Comment, Label | Org → Team → Board → Column → Issue → Comment; Issue ↔ Label (many-to-many) |
| **2** | + AgentKey, Automation, WebhookSource, AuditLog (expanded) | AgentKey → Team; Automation → Board; WebhookSource → Team |
| **3** | + ComplianceTier, AuditExport, EHRConnection, AnalyticsReport | ComplianceTier → Organization; EHRConnection → Team |

**AI Agent Rule:** Every new table MUST include `teamId` (for RLS), `createdAt`, `updatedAt`, `createdById`. Tables that record mutations MUST include `actorType` (human \| agent \| automation \| system).

### 5.2 Issue Ordering

LexoRank-style float ordering for both `Column.order` and `Issue.order`:

| Requirement | Implementation |
|-------------|---------------|
| Drag-and-drop reorder | Float value between adjacent items (1.0, 2.0, 3.0 → insert 1.5 between 1 and 2) |
| No full table scan on reorder | Update only the moved item's `order` value |
| Rebalance when precision runs out | Background job detects gaps < 0.001; reassigns evenly-spaced floats |
| Agent reorder | Same mechanism — agents call `PATCH /issues/:id` with `{ order: 1.5, columnId: "..." }` |

### 5.3 Compliance Architecture

| Control | Phase | Implementation |
|---------|-------|---------------|
| **RLS** | 1 | Supabase Row Level Security on all `teamId`-scoped tables |
| **Soft deletes** | 1 | `deletedAt DateTime?` — no hard delete of user data without explicit compliance review |
| **Audit log** | 1–2 | `AuditLog` table: every create/update/delete logged with actor, timestamp, diff |
| **PHI field controls** | 3 | Column-level encryption for issues flagged as containing PHI (compliance tier only) |
| **Data residency** | 3 | Enterprise option: Supabase region selection at org creation |
| **BAA** | 3 | DocuSign BAA flow gated by `ComplianceTier.hipaaEnabled` |

### 5.4 Design System

| Principle | Implementation |
|-----------|---------------|
| **Keyboard-first** | Every action has a keyboard shortcut. Tab order is logical. Focus trapping in modals (Radix UI). |
| **Density options** | Compact / Comfortable / Spacious view on board. Issue density affects padding, not data. |
| **Color system** | shadcn/ui tokens only (`--primary`, `--background`, `--accent`, etc.). Never hardcode hex in components. |
| **Status colors** | Labels use system-defined palettes (not arbitrary hex). Color-blind accessible. |
| **Agent attribution** | Issues created by agents show a robot icon badge. Automations show a lightning bolt. |

---

## 6. FRACTAL Agent Integration

TaskFlow is designed to be a natural target for FRACTAL sub-agents. A FRACTAL Feature Lead agent assigned to an epic can:

1. **Read current work state:** `GET /api/issues?boardId=...&status=in_progress`
2. **Create new issues:** `POST /api/issues` with `{ title, description, priority, source: "agent", agentId }`
3. **Move issues through workflow:** `PATCH /api/issues/:id` with `{ columnId }` when work completes
4. **Post progress updates:** `POST /api/issues/:id/comments` with PULSE-style updates
5. **Close completed work:** `PATCH /api/issues/:id` with `{ status: "done" }`

**Why this matters:** The FRACTAL system already uses HANDOFF.md and PULSE.md for agent communication. TaskFlow provides a human-visible, persistent board where that same work is tracked. Humans see progress without reading markdown files in `.claude/FRACTAL/workstreams/`.

**Integration Pattern:**
```
FRACTAL Architect creates BLUEPRINT.yaml
  → Feature Lead agent reads blueprint
  → Feature Lead creates TaskFlow issues for each workstream
  → Sub-agents update issue status as they work
  → Humans see live board reflecting FRACTAL state
  → Feature Lead closes issues when workstream COMPLETE
```

---

## 7. Decision Principles for AI Agents

When writing code, reviewing PRs, or making architectural choices, apply these in priority order:

### Tier 1 — Absolute Rules (Never Violate)

| Rule | Rationale |
|------|-----------|
| **All data scoped to `teamId`** | Multi-tenancy. Data leakage between teams is a security incident. RLS enforces at DB level. |
| **Auth before any DB operation** | Server Actions and API routes check session/API key before touching the database. |
| **Soft deletes only** | Audit trail requirement. Hard delete only with explicit compliance flag + owner-only permission. |
| **No PHI in issue titles by default** | Issues are not a clinical record system. Phase 3 compliance tier handles PHI fields with encryption. |

### Tier 2 — Strong Preferences (Deviate Only With Documented Justification)

| Preference | Rationale |
|------------|-----------|
| **Float ordering over integer rank** | LexoRank-style avoids full-table reorder on drag-and-drop. Integer rank requires renumbering all siblings. |
| **Feature flags over branches** | Decouple deployment from release. Clinical workflow templates should be toggleable per-team. |
| **Server Actions for all mutations** | Consistent auth, validation, and error handling. No ad-hoc `fetch()` mutations from Client Components. |
| **Stamp actor on all mutations** | `actorType` + `actorId` on every write enables audit trail with no extra work later. |

### Tier 3 — Guidelines (Use Judgment)

| Guideline | Context |
|-----------|---------|
| **Prefer shadcn/ui components** | Use shadcn/ui for standard UI patterns. Custom-build only for domain-specific components (kanban card, command palette item). |
| **API-first design** | Every mutation via Server Action should also be callable via the public REST API. No "UI-only" data paths. |
| **Test with realistic fixtures** | Don't test issue creation with `{ title: "test" }`. Use fixtures that match real healthcare team names, priorities, and workflow states. |

---

## 8. Competitive Context

| Competitor | Their Strength | Our Differentiation |
|-----------|---------------|---------------------|
| **Linear** | Best-in-class engineering UX, speed, keyboard shortcuts | We match UX quality AND add healthcare compliance tier + FRACTAL agent-native API |
| **Jira** | Enterprise features, Atlassian ecosystem | We are 10x lighter. No XML config. Self-hostable. Agents can use us without Scriptrunner. |
| **Asana** | General-purpose, clinical ops teams use it | We have workflow templates purpose-built for healthcare ops (PA queues, CDI worklists) |
| **GitHub Projects** | Free for engineering, tied to GitHub | We span engineering AND clinical ops in one board. No GitHub dependency for clinical teams. |
| **Notion** | Flexible, some teams use it for task tracking | We are faster, keyboard-first, and have structured issue lifecycle (not freeform blocks). |

---

## 9. Roadmap Summary

```
Q1-Q2 (Now)          Q3-Q4                2 Years              3+ Years
────────────────────┬─────────────────────┬─────────────────────┬──────────────
PHASE 1             │ PHASE 2             │ PHASE 3             │ PHASE 4+
                    │                     │                     │
Core Data Model     │ FRACTAL Agent API   │ HIPAA BAA Tier      │ Extension API
                    │                     │                     │
Board + Issue CRUD  │ Workflow Templates  │ Audit Trail Export  │ App Marketplace
                    │                     │                     │
Drag-and-Drop       │ AI Issue Triage     │ EHR Webhooks        │ Data Flywheel
                    │                     │                     │
Command Palette     │ Automations         │ Clinical Analytics  │
                    │                     │                     │
Team Auth + RLS     │ Inbound Webhooks    │ SSO + SCIM          │
                    │                     │                     │
REST API            │ Audit Log v2        │ Platform Shell      │
                    │                     │                     │
Self-Host Docs      │                     │                     │
────────────────────┴─────────────────────┴─────────────────────┴──────────────
Pattern:              Composable /          Compound               Modular Suite
                      Headless              Startup
```

---

## 10. Document Governance

| Item | Detail |
|------|--------|
| **Owner** | Head of Product + CTO / Tech Lead |
| **Review cadence** | Monthly, or after any major architecture decision |
| **AI Agent access** | Include in context for all architecture-related prompts |
| **Change process** | Proposed changes must include: what's changing, why, which phase it affects, and whether it conflicts with existing decisions |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-16 | Initial version. Healthcare kanban SaaS framing: Linear for healthcare teams, FRACTAL agent-native, phased compliance roadmap. |
