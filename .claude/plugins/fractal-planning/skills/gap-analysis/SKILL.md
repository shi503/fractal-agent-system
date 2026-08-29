---
name: gap-analysis
description: "Run a structured gap analysis at a milestone boundary. Evaluates current state against external benchmarks, internal parity targets, quality and compliance gates, and demo readiness. Produces a prioritized gap inventory with effort estimates and blocking dependencies. Use when the user asks to run a gap analysis, audit milestone readiness, check parity against a reference implementation, or answer how far from done a milestone is."
user-invocable: true
argument-hint: "[milestone name or slug] — e.g., 'M1', 'core-data-model', or leave blank to be asked"
---

# Gap Analysis — Milestone Evaluation

You are conducting a structured gap analysis for this project at a milestone boundary. This is a quality gate — be honest, specific, and file-path precise.

## Context Files (Read First)

1. `.claude/fractal/STRATEGIST-<project>.md` — the Tier-0 intent doc. It defines the milestone set, the evaluator archetypes, and the gap-analysis cadence. Read its milestone section before anything else.
2. `standards/engineering-principles.md` and `standards/architecture-patterns.md` — the bar you are measuring against.
3. Any prior gap analysis under `.claude/fractal/gap-analyses/` — read the most recent for methodology and to see which gaps were already logged. A gap that reappears unchanged is itself a finding.

If the project has no STRATEGIST doc, ask the user for the milestone definition rather than inventing one.

## Step 1: Identify Milestone and Scope

Ask the user which milestone this gap analysis targets, or infer it from the invocation argument plus the STRATEGIST doc's milestone list. Typical shapes:

- **Foundation milestone** — core data model, auth, and the first end-to-end path
- **Workflow milestone** — the primary user workflow running under production conditions
- **Platform milestone** — shared services, extension points, multi-consumer readiness
- **Custom** — user-defined scope

Restate the scope in one sentence and get agreement before auditing. A gap analysis with fuzzy scope produces an inventory nobody can act on.

## Step 2: Audit Current State

For the milestone scope, perform a thorough codebase audit. The four reads below are categories, not filenames — adapt them to the stack in front of you:

1. **Entry-point map** — inventory every route, command, or public entry point in milestone scope, read from the actual router/registry file rather than from documentation.
2. **Surface inventory** — for each entry point, list the modules or components behind it, their line counts, and functional status (Working / Partial / Shell).
3. **Backend coverage** — check the server-side route or handler tree for endpoint completeness against the surfaces above.
4. **State and service coverage** — verify a store or service exists for every data flow the milestone claims, and that nothing is still reading from a mock.

Cite `file:line` for every claim. "Looks implemented" is not an audit result.

## Step 3: Evaluate Against Four Lenses

### Lens 1: External Benchmark
Compare against best-in-class products in the same category:
- What would a practitioner evaluating this kind of product expect to see?
- What signals "production-grade" versus "prototype"?

### Lens 2: Internal Parity
Compare against the project's reference implementation — the prior app, the design prototype, or the sibling surface this milestone is meant to match. If the STRATEGIST doc names no reference, ask the user for one; cite it by repo-relative path.
- Feature parity matrix: ✅ (matches, functional) / ⚠️ (works, differs) / ❌ (missing)
- Do a second-pass code read — first-pass assessments routinely miss behavioral gaps that only appear when you trace a data flow end to end.

### Lens 3: Quality and Compliance Gate
Evaluate the controls actually in scope for *this* milestone — not the whole compliance program:
- Authentication and session management
- Data access controls (tenant/row scoping, authorization boundaries)
- Audit logging
- Sensitive-data boundaries — no secrets or personal data in URLs, logs, or error payloads
- Key and credential management

### Lens 4: Demo Walk-Through
Simulate a 30-minute live demo with a skeptical evaluator:
- What breaks or looks unfinished?
- What requires hidden knowledge to navigate?
- Where does the experience signal "prototype"?

## Step 4: Produce Gap Inventory

Write the gap analysis to `.claude/fractal/gap-analyses/{YYYY-MM-DD}-{milestone-slug}.md` (create the directory if it does not exist), using this structure:

```markdown
# Gap Analysis — [Milestone Name]

**Status:** In Progress
**Created:** [date]
**Milestone:** [name / slug]
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
**Implementation approach:** [module structure, data flow]
**What NOT to do:** [antipatterns to avoid]

## Scoring Matrix
| ID | Gap | Priority | Effort | Blocks | Status |
|----|-----|----------|--------|--------|--------|

## Quality Gate Results
| Control | Status | Evidence |
|---------|--------|----------|

## Effort Summary
| Priority | Count | Total Effort |
|----------|-------|-------------|
```

## Scoring Rules

**Priority:**
- **P0 / CRITICAL** — Breaks during a live demo walk-through, or is a data-integrity / security issue
- **P1 / HIGH** — Signals "prototype" to an evaluator, or blocks other gaps
- **P2 / MEDIUM** — Polish, consistency, perceived maturity
- **P3 / LOW** — Nice-to-have, appropriate for a later phase

**Effort:**
- **XS:** 15-30 minutes
- **S:** 1-2 hours
- **M:** 4-6 hours (half day)
- **L:** 1-2 days
- **XL:** Multi-day or sprint-sized

**Status tracking:** Update the document inline as gaps are resolved. Use ✅ ⚠️ ❌ in the parity matrix. The document is the living tracker.

## Output

1. The gap analysis document under `.claude/fractal/gap-analyses/`
2. If gaps are large enough, workstream PRD stubs for the major remediation efforts
3. A recommended sprint sequence based on blocking dependencies
4. A summary for the Architect: gap count by priority, estimated total effort, recommended next milestone gate

## Gotchas

- **Scope creep in the audit.** A gap analysis of "the whole product" produces an inventory nobody acts on. Hold the milestone boundary you agreed in Step 1.
- **First-pass optimism.** The most common defect in this skill's output is grading a surface "Working" from its route registration alone. Trace one real data flow per surface before grading it.
- **Do not commit.** This skill writes the document; the Architect owns commits and router state.
