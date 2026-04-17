# CLAUDE.md Scoring Rubric

**Status:** Reference
**Version:** 1.0
**Created:** 2026-04-14
**Used by:** `.claude/skills/claude-md-audit/` — invoke that skill to score a CLAUDE.md against this rubric.
**Informed by:** [`docs/research-claude-code-harness.md`](./research-claude-code-harness.md) §3 (CLAUDE.md conventions), §10 (output discipline), §12 (verification agent clauses).

---

## Purpose

`CLAUDE.md` is the single highest-leverage piece of context a project can maintain for an agent harness. The Claude Code system prompt auto-loads it every turn; FRACTAL's Architect reads it before decomposing any epic; Feature Leads treat it as ground truth. A weak CLAUDE.md costs every downstream agent invocation. A strong CLAUDE.md pays back on every turn forever.

This rubric scores a CLAUDE.md across 12 dimensions on a 0/1/2 scale. Maximum raw score: **24**. The audit skill converts that into a percentage and surfaces the three lowest-scoring dimensions as the primary improvement targets.

---

## Scoring model

| Score | Meaning |
|:---:|---|
| **0** | Absent or actively misleading |
| **1** | Partial — present but incomplete, generic, or unstructured |
| **2** | Strong — specific, structured, and actionable for an agent |

**Quick-read band:**

| Total | Band | Interpretation |
|:---:|---|---|
| 22–24 | A | Near-ideal; only polish items remain |
| 18–21 | B | Solid foundation; 2–3 dimensions need work |
| 12–17 | C | Half the value is missing; prioritize rewrite |
| 6–11 | D | Barely grounds the agent; heavy drift risk |
| 0–5 | F | File exists but is noise; agent will hallucinate freely |

---

## Dimension 1 — Role & Persona Clarity

Does the file open with a specific, first-person-addressed role for the agent?

| Score | Anchor |
|:---:|---|
| 0 | No role; file jumps straight into tech details |
| 1 | Generic role ("You are a helpful coding assistant") |
| 2 | Specific role + stack + goal statement + explicit trade-offs the agent should make |

**Positive example** (from `.claude/CLAUDE.md`):
> "**You are a dedicated Next.js 15 developer** building TaskFlow... You leverage React Server Components for initial data loading, Server Actions for all mutations... Your goals: ship fast, maintain clean code, keep infra costs low, avoid regressions."

**Negative example:** "This is the docs for our app."

**Remediation template:**
```markdown
## Your Role & Persona
You are a dedicated **{stack}** developer building **{product}** — {one-line elevator pitch}.
Your goals: **{3-4 explicit trade-offs, e.g. ship fast / avoid regressions / keep costs low}**.
You work with {collaborator} who {drives priorities / owns decisions}.
```

---

## Dimension 2 — Product Identity & Users

Does the agent know *who* the software is for and *what* "good" means to them?

| Score | Anchor |
|:---:|---|
| 0 | No product framing |
| 1 | One-liner description |
| 2 | ICP, strategic positioning, explicit non-goals / "not a clone of X" framing |

**Positive example:** "Strategic Position: 'The Linear for self-hosters' — not a Jira clone, not a Trello clone. Speed and keyboard navigation are non-negotiable differentiators."

**Why it matters:** When the agent faces a UX or architecture judgment call, it needs to resolve against the product's values, not generic best practice.

---

## Dimension 3 — Tech Stack (Versioned Table)

| Score | Anchor |
|:---:|---|
| 0 | No stack listed |
| 1 | Prose list ("we use Next.js and Postgres") |
| 2 | Versioned table with per-layer notes explaining choice / constraint |

**Positive example:** the stock `.claude/CLAUDE.md` stack table includes `Next.js 15.x`, `TypeScript 5.x strict`, `Prisma 6.x` with inline notes like `schema.prisma is the source of truth`.

**Why a table?** Agents parse tables reliably; prose stack descriptions decay into hallucinated versions within a few turns.

---

## Dimension 4 — Essential Commands

| Score | Anchor |
|:---:|---|
| 0 | No commands listed |
| 1 | A handful, uncategorized |
| 2 | Grouped by purpose (dev / build / test / db), each annotated, **CI gate explicitly spelled out** |

**Positive example:**
```bash
> CI gate: npm run build && npx tsc --noEmit && npm run lint && npm run format:check && npm run test:run must all pass.
```

The CI-gate line is load-bearing — it's what lets a Feature Lead know when it is *actually* done vs. "looks done." Refer to the Verification Agent lines in `research-claude-code-harness.md` §12.

---

## Dimension 5 — Project Structure (Annotated Tree)

| Score | Anchor |
|:---:|---|
| 0 | No layout info |
| 1 | Top-level directories listed |
| 2 | Nested tree with per-directory purpose comments |

**Why:** an unannotated tree means the agent spends tool calls re-discovering what each directory is for on every session. An annotated tree collapses that to zero tool calls.

---

## Dimension 6 — Decision Trees / Rules

| Score | Anchor |
|:---:|---|
| 0 | No explicit decision rules |
| 1 | Prose rules ("prefer X over Y") |
| 2 | Decision tables or ASCII decision trees covering recurring judgment calls |

**Positive example:** the stock file has a "Component Decision Tree" (when to use `"use client"`) and a "State Management Decision Tree" (RSC vs. TanStack Query vs. Zustand). Both are tables.

**Why tables:** LLMs follow explicit if/else branches more reliably than implicit prose preferences.

---

## Dimension 7 — Canonical Code Patterns

| Score | Anchor |
|:---:|---|
| 0 | No code examples |
| 1 | One or two snippets |
| 2 | Copy-paste templates for every mutation/query/flow type with inline comments explaining each step |

**Positive example:** the stock file's `createIssue` Server Action template — numbered comments mark the required steps (auth → validate → business logic → revalidate → return). New mutations inherit the shape.

**Why:** code patterns embedded in CLAUDE.md anchor the agent's style. Without them, each generated function drifts.

---

## Dimension 8 — Forbidden Patterns (with Reasons)

| Score | Anchor |
|:---:|---|
| 0 | No forbiddens listed |
| 1 | Bullet list ("don't use X") |
| 2 | Table: **pattern · why it breaks · use instead** |

**Positive example:** the stock file's `Forbidden Patterns` table — 13 rows, each with a concrete failure mode and a named replacement.

**Why the 3-column table:** the *why* is what lets the agent handle edge cases; the *use instead* is what prevents it from just removing the forbidden thing without replacing it.

---

## Dimension 9 — Security & Secrets Posture

| Score | Anchor |
|:---:|---|
| 0 | No mention of security |
| 1 | Mentions secrets generically |
| 2 | Explicit rules for: env vars, logging, error messages, public-vs-private env, boundary definition |

**Positive example:** the stock file's 6-bullet security section covering PII logging, error sanitization, RLS enforcement, and `NEXT_PUBLIC_*` visibility.

---

## Dimension 10 — Git / Commit Conventions

| Score | Anchor |
|:---:|---|
| 0 | Absent |
| 1 | Informal hint ("use good commit messages") |
| 2 | Conventional Commits + branch naming + commit gate + one-logical-change rule |

---

## Dimension 11 — Harness Integration

Does the file explicitly tell agents *how it fits into the broader harness* (FRACTAL, Superpowers, gstack, plain Claude Code)?

| Score | Anchor |
|:---:|---|
| 0 | No mention of the harness |
| 1 | Harness is named but integration isn't described |
| 2 | Explicit: which agents read this file, which other docs are authoritative, how workstreams flow, where handoffs go |

**Positive example:** the stock file's `FRACTAL Integration` section names the Strategist doc path, BLUEPRINT path, workstreams directory, and the rule that "no workstream is marked COMPLETE without a passing build."

**Why it's load-bearing:** in multi-agent systems, a CLAUDE.md that doesn't explain the agent tiering means each tier re-invents rules on the fly.

---

## Dimension 12 — Token Hygiene

| Score | Anchor |
|:---:|---|
| 0 | >1000 lines, or everything inlined (deep-dive guides, full API refs inside CLAUDE.md) |
| 1 | 300–1000 lines, some unnecessary inlining |
| 2 | ≤300 lines, deep content linked out to `.SPECS/guides/*` or `docs/*` |

**Why:** CLAUDE.md is reloaded every turn. Every extra line is paid on every tool call. The stock advice ("reference by path, don't paste inline") is the right rule.

**Measurement:** count lines of CLAUDE.md; count lines of external guide files it links to. A healthy ratio is 1:5 or better (CLAUDE.md is a table of contents, not the full manual).

---

## Bonus — "Agent Output Discipline" (Dimension 13, advisory)

**Not scored in the baseline rubric** — this is forward-looking based on `research-claude-code-harness.md` §10. The public source analysis showed a 1.2% token reduction from replacing generic "be concise" directives with **explicit numeric word caps**.

**Advisory anchor:**
- **Present (+1 advisory point):** CLAUDE.md includes explicit output caps, e.g. "responses ≤100 words; intermediate status ≤25 words; no opening affirmations; no trailing summaries."

Projects that care about token cost or latency should add this; it is not required for the core score.

---

## How the skill uses this rubric

The `claude-md-audit` skill reads this file verbatim, then:

1. Reads the target CLAUDE.md.
2. For each of dimensions 1–12, assigns 0/1/2 with an evidence quote (or "not found").
3. Computes total / 24 and letter band.
4. Selects the three lowest-scoring dimensions.
5. For each of those three, generates a **before/after diff** showing a concrete rewrite.
6. Writes the audit report to `docs/claude-md-audits/{YYYY-MM-DD}-{project}.md`.

---

## Change log

- **2026-04-14 v1.0** — Initial rubric. Derived from Claude Code harness research and the existing TaskFlow `.claude/CLAUDE.md` as a reference exemplar.
