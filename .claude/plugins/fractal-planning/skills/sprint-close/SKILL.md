---
name: sprint-close
description: "End-of-sprint ritual orchestrator. Walks six grounded stages — weekly digest, deferral sweep, retro capture, forward plan, improvement cycle, and a grounded demo brief built LAST — by composing existing planning skills rather than re-synthesizing. The demo brief inherits upstream grounding so it can't drift into over-confident fresh synthesis. Invoke at a sprint boundary. Use when the user asks to close the sprint, close out the sprint, run the end-of-sprint ritual, run the sprint retro, or wrap up the sprint."
user-invocable: true
argument-hint: "[--from YYYY-MM-DD] [--to YYYY-MM-DD] [--sprint <name>] — defaults to the last 7 days"
---

# sprint-close — end-of-sprint ritual

You are the **planning assistant** running the team's end-of-sprint ritual. Your job is to produce a grounded sprint-close package by **composing existing skills in order** — you are glue and discipline, not a new synthesis engine.

**Core principle (the reason this skill exists):** the demo/exec brief is built **LAST**, from already-grounded upstream artifacts — never as a fresh synthesis. Synthesizing a brief from ticket titles, a git log, and one stale doc reliably produces over-confident, wrong claims: the ticket says Done, the doc says shipped, and neither is true on the branch being demoed. Each stage below produces grounded material the brief inherits.

## Inputs

- `--from` / `--to` (ISO 8601). Default: last 7 calendar days ending today.
- `--sprint <name>` (optional): label for the sprint. If given, prefer the sprint's actual start/end dates over the 7-day default.

If invoked bare, use defaults and state the window you chose.

## The six stages (run in order)

### 1. Digest
Invoke `/weekly-digest` over the window. Capture its output — new sources, decision activity, open OQs, active locks. That output is already grounded: it reads the decision log, the wiki operation log, and git. Do not re-derive what changed; use the digest.

### 2. Deferral sweep
Scan the sprint's HANDOFFs, queue, and open work for deferrals. For each one, confirm it has **a named owner AND a home** — a backlog row or a named follow-on workstream, with an absolute revisit date, not "later" or "next sprint". **Unowned or homeless deferrals are scope drops**: list them as blockers rather than letting them pass silently. This stage is what catches a silent scope drop before it is discovered mid-demo.

### 3. Retro capture
Produce a short, honest retro: what went well, what didn't, and the concrete learnings. Be specific and non-performative — name the actual failure and its mechanism, not a vague "be more careful". Each learning must be actionable in stage 5.

### 4. Forward plan
Seed the next sprint from: open OQs (stage 1) + unfinished or deferred items (stage 2) + retro learnings (stage 3). Output a candidate next-sprint list, each item carrying a rationale tied to its source stage.

### 5. Improvement cycle
Promote retro learnings into durable artifacts, routing each by ownership and authority rather than by whichever store is easiest to write:
- A correction to how the agent works → an agent `feedback` memory.
- A team convention or piece of shared knowledge → the wiki (`wiki-add` → `wiki-ingest`).
- A decision → flag it for the promote-to-ledger flow. Never auto-lock; the ledger's RACI gate exists for exactly this.
- A tooling change → a backlog item, or an edit to the rule or skill that misfired.

State where each learning went. A learning with no destination did not survive the sprint.

### 6. Grounded demo brief (LAST)
Invoke `/stakeholder-brief` (exec snapshot) for the audience. **Every claim must be grounded before it ships.** Ground each claim against:
- (a) the **build state of the branch actually being demoed** — not "the PR that merged somewhere";
- (b) decision **Status**, not decision existence — a decision record can exist while its status is still proposed or blocked;
- (c) the **deferral queue** from stage 2 — a ticket can read Done while the behaviour is gated.

Tag every claim **[grounded]** or **[unverified]**. When in doubt, write "unverified" — never upgrade an unverified claim into confident prose.

## Output

Print the package to chat (paste-ready), in this order: **Digest → Deferral sweep (with any blockers flagged) → Retro → Forward plan → Improvement-cycle routing → Grounded brief**. Write to a file only if the user asks. The brief section, if it goes to executives, should be a thin grounded snapshot — pair it with a demo recording link if one is provided.

## Gotchas

- **Do NOT skip to stage 6.** The whole point is that the brief is built last from grounded upstream artifacts. A brief written first, or in isolation, is exactly the failure this ritual prevents.
- **Compose, don't reimplement.** Invoke `weekly-digest` and `stakeholder-brief` — do not re-write their logic inline. If they need changes, change them, not this skill.
- **Grounding is branch-aware.** "Merged to the main line" ≠ "true on the demoed branch." Check what the demo actually runs (`git ls-tree <demoed-branch>`).
- **Decision Status, not existence.** A decision record or ticket existing is not a decision made. Read the status block and the deferral queue.
- **Never auto-lock decisions.** Stage 5 *flags* decision candidates for promotion; a human with the accountable role signs off. Same for promoting a memory into team knowledge.
- **Deferrals need absolute dates.** "Next sprint" rots — require `YYYY-MM-DD`.
- **Scheduling is out of scope here.** This skill is trigger-agnostic; how it fires (manually, on a schedule, or from cron) is a separate concern.
