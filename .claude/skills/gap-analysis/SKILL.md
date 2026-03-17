---
description: "Run a structured gap analysis at a milestone boundary. Evaluates current state against external benchmarks, internal parity targets, compliance gates, and demo readiness. Produces a prioritized gap inventory with effort estimates and blocking dependencies."
user-invocable: true
---

# Gap Analysis — Milestone Evaluation

You are conducting a structured gap analysis for **{project}** at a milestone boundary. This is a quality gate — be honest, specific, and file-path precise. Replace `{project}` with your project name.

## Context Files (Read First)

1. Your project's Strategist document (e.g. `.claude/fractal/STRATEGIST-{project}.md`) — §8 defines milestones, evaluator archetypes, and gap analysis cadence
2. `{project-guides}/platform-strategy.md` (or equivalent) — platform evolution phases and decision principles
3. Previous gap analyses for methodology reference (if any), e.g. in `{project-specs}/PRD/` or `docs/gap-analysis/`

## Step 1: Identify Milestone and Scope

Ask the user which milestone this gap analysis targets (or infer from context):
- **Milestone 1:** [Customize — e.g. Core Go-Live: auth, billing, API, docs]
- **Milestone 2:** [Customize — e.g. Feature Complete: key workflows]
- **Milestone 3:** [Customize — e.g. Scale / Polish]
- **Custom:** User-defined scope

## Step 2: Audit Current State

For the milestone scope, perform a thorough codebase audit:
1. **Route map** — inventory every route (or equivalent) relevant to the milestone
2. **Component/screen inventory** — for each route, list components, their line counts, and functional status (Working / Partial / Shell)
3. **Backend/API coverage** — check routes or services for endpoint completeness
4. **State/data coverage** — verify stores and services exist for all data flows

## Step 3: Evaluate Against Four Lenses

### Lens 1: External Benchmark
Compare against best-in-class products in your category (e.g. Supabase, Stripe, GitHub, Linear, OpenAI, Vercel for SaaS):
- What would a technical evaluator expect to see?
- What signals "enterprise-grade" vs. "prototype"?

### Lens 2: Internal Parity
If you have a reference implementation or design spec to match:
- Feature parity matrix: ✅ (pixel-perfect + functional) / ⚠️ (works, differs) / ❌ (missing)
- Do a second-pass code read — first-pass assessments often miss behavioral gaps

_If no reference app, skip or replace with "design spec compliance" or "accessibility/UX checklist."_

### Lens 3: Compliance Gate
Evaluate controls scoped to this milestone (customize for your domain):
- Auth and session management
- Data access controls (e.g. RLS, org scoping)
- Audit logging
- Sensitive data boundaries (no PII/secrets in URLs, logs, errors)
- Key management

### Lens 4: Demo Walk-Through
Simulate a live demo with a technical buyer:
- What breaks or looks unfinished?
- What requires hidden knowledge to navigate?
- Where does the UX signal "prototype"?

## Step 4: Produce Gap Inventory

Write the gap analysis document to your project's spec directory (e.g. `{project-specs}/PRD/`, `docs/gap-analysis/`) following this structure:

```markdown
# Gap Analysis — [Milestone Name]

**Status:** In Progress
**Created:** [date]
**Milestone:** [1/2/3/Custom]
**Scope:** [brief description]

## Executive Summary
- Current parity estimate: X%
- Critical gaps: N
- Total gaps: N
- Blocking dependencies: [list]

## Feature Parity Matrix
| Feature | Status | Notes |
|---------|--------|-------|
| ... | ✅/⚠️/❌ | ... |

## Gap Inventory

### GAP-[ID]: [Title]
**Priority:** CRITICAL / HIGH / MEDIUM
**Effort:** XS / S / M / L / XL
**Blocks:** [list of GAP IDs this unblocks]
**Status:** Open

**What's missing:** [precise behavioral description]
**Source files:** [exact file paths with line references]
**Implementation approach:** [component structure, data flow]
**What NOT to do:** [antipatterns to avoid]

## Scoring Matrix
| ID | Gap | Priority | Effort | Blocks | Status |
|----|-----|----------|--------|--------|--------|

## Compliance Gate Results
| Control | Status | Evidence |
|---------|--------|----------|

## Effort Summary
| Priority | Count | Total Effort |
|----------|-------|-------------|
```

## Scoring Rules

**Priority:**
- **P0 / CRITICAL** — Breaks during a live demo walk-through, or data integrity/security issue
- **P1 / HIGH** — Signals "prototype" to a technical buyer, or blocks other gaps
- **P2 / MEDIUM** — Polish, consistency, enterprise perception
- **P3 / LOW** — Nice-to-have, Phase 2+ appropriate

**Effort:**
- **XS:** 15-30 minutes
- **S:** 1-2 hours
- **M:** 4-6 hours (half day)
- **L:** 1-2 days
- **XL:** Multi-day or sprint-sized

**Status tracking:** Update the document inline as gaps are resolved. Use ✅ ⚠️ ❌ in the parity matrix. The document is the living tracker.

## Output

1. The gap analysis document in your project's spec/output directory
2. If gaps are large enough, sub-PRDs or tickets for major remediation efforts
3. A recommended sprint sequence based on blocking dependencies
4. Summary for the Architect: gap count by priority, estimated total effort, recommended next milestone gate
