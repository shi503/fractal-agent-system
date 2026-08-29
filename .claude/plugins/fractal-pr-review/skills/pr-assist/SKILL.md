---
name: pr-assist
description: "Early PR-review pass — gather a PR's diff + existing reviewer threads + CI state, run the bundled reviewers (pr-review-toolkit + peer-review), triage all findings into a severity-ranked table with file:line + concrete fix + drafted plain-English reply, cross-check the accruing standards/pr-review-guides/ library for recurrences, and log each finding-class back so recurring findings compound into team guidance. Never posts to GitHub — output is human-curated. Use when the user asks to run pr-assist, do an early review pass, pre-review this PR, or review this PR before it goes out."
user-invocable: true
---

# pr-assist — early PR-review pass

`/pr-assist <PR# | "in-review" | branch>`

Runs an early review pass on one PR (or every open non-draft PR) and produces a curated report. **It never posts to GitHub** — the human/architect curates and posts. Drafted replies are plain-English (no internal shorthand codes — write as if explaining to a new teammate).

## Workflow

### 1 — Gather
- `gh pr diff <N>` — the diff under review.
- `gh api repos/{owner}/{repo}/pulls/<N>/comments` + `.../reviews` — existing reviewer threads, so the pass triages own + existing findings together and never contradicts a standing thread.
- `gh pr checks <N>` (or `gh pr view <N> --json statusCheckRollup`) — CI state.
- For `in-review`: `gh pr list --state open --draft=false` and loop.

### 2 — Run the bundled reviewers
Dispatch these against the gathered diff (via the Agent tool / Skill tool — they are installed alongside this bundle):
- `pr-review-toolkit:code-reviewer` — correctness, security, edge cases.
- `pr-review-toolkit:silent-failure-hunter` — swallowed errors, empty catches, inappropriate fallback.
- `pr-review-toolkit:pr-test-analyzer` — coverage gaps, missing failure-path tests.
- `peer-review` (fractal-tools) — verify each EXISTING reviewer claim against the actual code (some reviewer comments are wrong; confirm before echoing).

Run independent reviewers in parallel where possible.

### 3 — Triage
Merge own findings + existing reviewer threads into one **severity-ranked table**, de-duped (same file:line + same class collapses):

| Sev | Finding | File:line | Class | Fix | Drafted reply |
|-----|---------|-----------|-------|-----|---------------|
| P1 | … | `x.ts:117` | `xss-bypasssecuritytrust` | concrete fix | plain-English thread reply |

Severity: **P1** = security / data-loss / silent failure on a real path; **P2** = correctness or missing failure-path test; **P3** = nit / style / duplication.

### 4 — Cross-check the guide library
For each finding, match its **class** against `standards/pr-review-guides/<class>.md`. If the class has prior occurrences, flag the recurrence in the table ("3rd `bypassSecurityTrustHtml` finding — see guide"). This is the compounding-value step: recurring classes become known anti-patterns.

Search the directory directly (`grep`/`ls standards/pr-review-guides/`) rather than bulk-reading every file. Cite `file:line`.

### 5 — Log back (the compounding value)
For each finding-class touched, append to `standards/pr-review-guides/<class>.md` (create from the template below if absent). This is a standards-library write; it is NOT a decision-log write and NEVER auto-locks anything. Bump `occurrences` and append a `Seen in` row.

### 6 — Output
A per-PR report: the severity table, the suggested fixes, the drafted replies, and the recurrence flags. Stop there. **Do not `gh pr review` / `gh pr comment`.** Hand the report to the human to curate and post.

## Finding-class guide schema — `standards/pr-review-guides/<class>.md`

```
---
class: xss-bypasssecuritytrust | info-leak-backend-detail | adapter-boundary-bypass | missing-service-test | flaky-test-timeout | double-audit-event | ...
severity: P1|P2|P3
occurrences: <n>
status: ACTIVE
---
## Pattern
<what it looks like in code>
## Why it's wrong
<rationale>
## Canonical fix
<the fix, with a code exemplar>
## Seen in
- <repo>#<PR> (<date>) — <file:line>
```

Over time this becomes the team's "things our reviews keep catching" guide — feedable into CLAUDE.md / dev guides.

## Defaults
- **Home:** plugin `fractal-pr-review` (this) — bundles the reviewers + carries the standards-library sink.
- **Sink:** `standards/pr-review-guides/` (dedicated dir).
- **Trigger:** manual `/pr-assist` only. A "PR opened/ready" hook is a later add, once trusted.
- **Auto-post:** never. Replies are drafted for a human to post.

## Boundaries
- Read-only against sibling repos + GitHub. No `gh` write subcommands.
- Reuses installed reviewer skills/agents — this bundle ships no agents of its own.
- Requires `standards/pr-review-guides/` for steps 4–5; degrades to steps 1–3 (report only, no guide library) if the directory is absent from a given repo.
