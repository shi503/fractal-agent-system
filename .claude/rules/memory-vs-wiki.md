paths: ["fixtures/taskflow/wiki/**", "tools/decision-ledger/**", "standards/**"]
---

# Session Notes vs Wiki vs Decision Ledger — what goes where

**Rationale:** it is always cheaper to keep a fact in your own head or a scratch note than to
file it properly — but a fact only you (or only this session) can see is invisible to a
teammate's agent working the same project tomorrow. Route a fact by who needs it to be
correct, not by which store is easiest to write to right now.

## The test (apply before writing anything durable)

**"Would another teammate's agent need this to be correct about the project?"**

- **No** → it is session-local. Keep it in your own working notes; do not commit it as a
  wiki page or a decision-ledger entry.
- **Yes** → it is team-relevant. File a copy in the substrate that matches its kind (below).

## Routing table

| Kind of fact | Home | How |
|---|---|---|
| Captured source material (a transcript, a spike's raw notes) | `wiki/raw/` (fixture: `fixtures/taskflow/wiki/raw/`) | `wiki-add` / `wiki-ingest` / `transcript-ingest` (`fractal-wiki` plugin) |
| Distillation of one source, or a cross-cutting synthesis | `wiki/sources/` or `wiki/synthesis/` | `wiki-ingest`, subject to the review-queue gate on edits to existing pages — see `docs/wiki-conventions.md` |
| A change-managed decision with an owner and RACI | `tools/decision-ledger/` entries | `tools/decision-ledger/storage/cli.py`, validated by `tools/decision-ledger/schema/validate.py` — see `.claude/rules/decision-ledger.md` |
| A cross-project coding standard or reusable convention | `standards/` | Edited directly, by review — see `standards/project-maintenance-model.md` |

## Promotion trigger

The moment a session-local note turns out to be team-relevant — a settled decision, a
convention others must follow, knowledge worth keeping — promote it: wiki for knowledge,
`tools/decision-ledger/` for decisions, `standards/` for conventions. A working note may
*cache* a decision, but the decision-ledger entry is canonical; on conflict the ledger wins
(live state > this file > git history — see `.claude/plugins/fractal-core/agents/feature-lead.md`
§0).

## Smell test

If you are about to write a project-specific fact into a personal or session-scratch note and
it would still matter next week to someone who isn't you, that is a promotion smell — it
belongs in wiki, the ledger, or `standards/`, not in a store only you can read.

<!-- referenced-paths
fixtures/taskflow/wiki
tools/decision-ledger
standards
docs/wiki-conventions.md
standards/project-maintenance-model.md
tools/decision-ledger/storage/cli.py
tools/decision-ledger/schema/validate.py
.claude/plugins/fractal-core/agents/feature-lead.md
-->
