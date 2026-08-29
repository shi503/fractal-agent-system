# HANDOFF — {WorkstreamName}

**Completed:** `YYYY-MM-DD`
**Blueprint:** `.claude/fractal/{BLUEPRINT-name}.yaml`
**Workstream PRD:** `.claude/fractal/workstreams/{kebab-name}.md`

> **This file is the approval gate.** The Architect evaluates this artifact against Layer 1 (deterministic) and Layer 2 (LLM-judgment) before marking the workstream COMPLETE. Do NOT generate this document if the CI gate is failing — fix the build first.

---

## 1. Summary of Work Completed

Factual list of concrete outcomes. Cite file paths for every meaningful change so a reviewer can jump directly to the diff.

- `path/to/file` — what changed and why
- …

Break into subsections (Phase 0, Task 1, Task 2, …) if the workstream had staged deliverables.

## 2. Summary of Work Not Completed

Tasks originally in scope that did not ship, and why.

- **Feature X** — deferred because … (link to the Out-of-Scope section of the PRD, or open a follow-up workstream).

If every AC shipped, write `None` explicitly.

## 3. Technical Debt Register

Shortcuts, workarounds, and deliberate imperfections introduced during this workstream. Each entry must state **what**, **why** (the pressure), and **remediation path** (when + who owns it).

- **What:** Example: error handling on the webhook ingest route is coarse.
  **Why:** the happy path covers the launch surface; time-boxed to ship the milestone.
  **Remediation:** Track in `.claude/fractal/ISSUES.md` or open a follow-up workstream before the next milestone gate.

## 4. Key Decisions Made

Decisions that deviated from the PRD or had meaningful downstream impact.

- **Decision:** …
  **Reasoning:** …
  **Impact:** …

Propagate any decision that touches architecture into this project's own decision record (issue tracker, ADR directory, or discovery log) so the Strategist sees it.

## 5. Deterministic Eval Results (Layer 1)

Evidence the CI gate passed. This HANDOFF is invalid if any primary gate fails.

| Command | Result | Notes |
|---|---|---|
| `{project build command}` | **PASS** / **N/A** | … |
| `{project lint command}` | **PASS** / **N/A** | … |
| `{project test command}` | **PASS** / **N/A** | `N/N` passing |
| `{project type-check command, if separate}` | **PASS** / **N/A** | … |

Adapt to the workstream scope (frontend-only, backend-only, docs-only). At minimum the primary build command must PASS. See `.claude/fractal/templates/prd-template.md` §4 for the CI gate this workstream committed to.

## 6. Verification for Reviewer

How the Architect (or a human reviewer) can confirm the claims above without re-running the whole workstream.

1. `git diff {base}..HEAD -- path/` — inspect the changed surface.
2. Run {smoke command} — confirms {behavior}.
3. Open {URL or file} — confirms {artifact} exists.

## 7. Next Steps / Handoff Notes

What the next workstream, reviewer, or maintainer should know.

- Downstream workstream: `{name}` may now start (its dependency is satisfied).
- Open questions surfaced: …
- Follow-up work logged in: `ISSUES.md` / new workstream PRD / discovery log.
