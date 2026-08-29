---
name: claude-md-audit
description: "Audits a CLAUDE.md file against the FRACTAL / Claude Code rubric and emits a scored report with prioritized, concrete improvement suggestions. Does not auto-apply edits. Re-runnable after each CLAUDE.md change. Use when the user asks to audit, score, or review a CLAUDE.md file."
user-invocable: true
---

# CLAUDE.md Audit

You are auditing a `CLAUDE.md` file — the always-on context anchor for an agent harness. This file is the highest-leverage piece of project context that exists; weak sections cost every downstream agent call, forever. Your job is to produce a **scored audit** with specific, actionable improvements.

## Context Files (Read First, in order)

1. [`docs/claude-md-rubric.md`](../../../../../docs/claude-md-rubric.md) — the **authoritative scoring rubric**. Read it in full. Your output must score every dimension it defines.
2. [`docs/research-claude-code-harness.md`](../../../../../docs/research-claude-code-harness.md) §3 (CLAUDE.md conventions), §10 (output discipline), §12 (Verification Agent) — the reasoning behind why each dimension matters. Cite when justifying a low score.
3. The target CLAUDE.md itself (default: `.claude/CLAUDE.md` at the repo root).

Do not proceed without reading the rubric. If it is missing, halt and report "rubric not found."

## Step 1: Identify the target

Ask the user which CLAUDE.md to audit unless they specified one. Common targets:

- `.claude/CLAUDE.md` — default
- `CLAUDE.md` at repo root — for projects not using the `.claude/` layout
- A path the user supplies

Also ask for the **project short-name** (used in the output filename). Default to the repo basename.

## Step 2: Score every rubric dimension

For each of the 12 dimensions in `docs/claude-md-rubric.md`:

1. Quote the relevant portion of the target CLAUDE.md (or write "not found").
2. Assign 0 / 1 / 2 using the anchors in the rubric.
3. Write a one-sentence justification grounded in the quoted evidence.

**Do not rubber-stamp.** If you can't find evidence in the file for a dimension, score 0 — do not infer. If the evidence is partial, score 1 and say what's missing to reach 2.

## Step 3: Compute score and band

- Raw total `/24`
- Percentage `= raw * 100 / 24` (rounded to nearest integer)
- Letter band using the rubric's quick-read band (A/B/C/D/F)
- **Advisory D13 (Output Discipline)** — score 0 or 1 per the rubric bonus. Report separately; do not add to the main 24-point total.

## Step 4: Pick top 3 improvement targets

Rules for selection:

1. Lowest-scoring dimensions first. Ties broken by **highest leverage** — dimensions 6 (decision trees), 7 (canonical patterns), 8 (forbidden patterns), and 11 (harness integration) have outsized impact and should jump the queue when tied.
2. Don't pick three dimensions that all require the same rewrite — spread the improvements.
3. If the file scores a B or higher but dimension 12 (token hygiene) is at 0–1, **always include it** in the top 3. Bloat compounds.

## Step 5: Generate concrete before/after edits

For each of the 3 targets:

- **Before:** the exact current state (quote or "not present").
- **After:** a full proposed replacement. No hand-waving — this should be copy-paste-ready.
- **Why:** one sentence tying back to a rubric anchor AND a harness-research section.

Do not auto-apply the edits. Leave them in the audit report for the user / Architect to accept.

## Step 6: Write the audit report

Write to `docs/claude-md-audits/{YYYY-MM-DD}-{project}.md`. Create the directory if it does not exist. Use this structure:

```markdown
# CLAUDE.md Audit — {project}

**Date:** YYYY-MM-DD
**Target:** {path to CLAUDE.md audited}
**Rubric version:** v1.0 (`docs/claude-md-rubric.md`)
**Auditor:** claude-md-audit skill

## Score

| Metric | Value |
|---|---|
| Raw | N / 24 |
| Percentage | NN% |
| Band | {A/B/C/D/F} |
| Advisory (D13 output discipline) | 0 / 1 |

## Dimension Scorecard

| # | Dimension | Score | Evidence |
|:---:|---|:---:|---|
| 1 | Role & persona clarity | 0/1/2 | "quote or 'not found'" |
| 2 | Product identity & users | 0/1/2 | ... |
| 3 | Tech stack | 0/1/2 | ... |
| 4 | Essential commands | 0/1/2 | ... |
| 5 | Project structure | 0/1/2 | ... |
| 6 | Decision trees / rules | 0/1/2 | ... |
| 7 | Canonical code patterns | 0/1/2 | ... |
| 8 | Forbidden patterns | 0/1/2 | ... |
| 9 | Security & secrets | 0/1/2 | ... |
| 10 | Git / commit conventions | 0/1/2 | ... |
| 11 | Harness integration | 0/1/2 | ... |
| 12 | Token hygiene | 0/1/2 | ... |

## Strengths

- 2-4 bullets calling out dimensions scored 2

## Top 3 Improvement Targets

### 1. Dimension N — {name}
**Current score:** X/2
**Before:**
> (exact quote or "not present")

**After:**
```markdown
(copy-paste-ready replacement)
```

**Why:** {rubric anchor + harness-research reference}

### 2. Dimension N — {name}
(same structure)

### 3. Dimension N — {name}
(same structure)

## Secondary Observations

- Any other dimensions where a small edit would jump the score
- Any drift concerns (sections that reference code paths that no longer exist)
- Any token-hygiene measurements (file line count; lines linked out vs inline)

## Recommended next action

One sentence: does this file need a heavy rewrite (C band or lower), targeted edits (B band), or maintenance only (A band)?
```

## Step 7: Report back to the caller

In chat, return:

1. The path of the written audit.
2. The three numbers: raw, percentage, band.
3. The three improvement-target dimension names.

Nothing else. The audit file is the deliverable.

## Output Discipline

Per `research-claude-code-harness.md` §10:
- Keep chat responses ≤100 words; intermediate status ≤25 words.
- No opening affirmations ("Great audit target!").
- No trailing summary of what the skill just did.

## What this skill does NOT do

- Does not auto-apply the suggested edits. The Architect / user accepts them.
- Does not re-score previous audits. Each run is a fresh point-in-time snapshot.
- Does not score dimensions outside the 12 listed in the rubric. If a new dimension is needed, update the rubric first.

## When to re-run

- After any non-trivial CLAUDE.md edit.
- At each milestone gate.
- When a new agent tier or harness pattern is adopted.
- Before using a project's CLAUDE.md as a template for a new project.
